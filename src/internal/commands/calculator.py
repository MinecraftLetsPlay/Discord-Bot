import discord
import math
import re
import logging
import sympy
import asyncio
import time
from sympy import solve, symbols, parse_expr, sympify, Number

# Copyright (c) 2025 Dennis Plischke.
# All rights reserved.

# -----------------------------------------------------------------------------
# Module: Calculator.py
# Description: A all around, text-based calculator capable of equation solving
# -----------------------------------------------------------------------------

# ----------------------------------------------------------------
# Component test function for calculator module
# ----------------------------------------------------------------

def component_test():
    status = "🟩"
    messages = ["Calculator module loaded."]
    
    return {"status": status, "msg": " | ".join(messages)}

# ----------------------------------------------------------------
# Additional Helpers and Globals
# ----------------------------------------------------------------

# Store last result for 'ans' functionality
LAST_RESULT = {}

# Security configuration
MAX_EXPRESSION_LENGTH = 500
CALCULATION_TIMEOUT = 5  # Seconds

# Checks if an expression is safe to evaluate
def is_safe_expression(expression):
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return False, "Expression too long (max 500 characters)"
        
    dangerous_keywords = ['import', 'eval', 'exec', 'open', '__', 'javascript:', 'js:', 'file:', 'ftp:', 'http:', 'https:', 'data:', r"\\x[0-9a-fA-F]{2}"]
    if any(keyword in expression.lower() for keyword in dangerous_keywords):
        return False, "Forbidden keywords detected"
        
    if expression.count('(') != expression.count(')'):
        return False, "Unbalanced parentheses"
        
    return True, ""

# Executes calculation with timeout
async def calculate_with_timeout(expression):
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: sympify(expression, locals=SAFE_FUNCTIONS)
            ),
            timeout=CALCULATION_TIMEOUT
        )
        
        # Format the result
        if isinstance(result, (int, float, Number)):
            return format_number(float(result))
        return str(result)
        
    except asyncio.TimeoutError:
        raise CalculatorError("Calculation timed out")
    
# ----------------------------------------------------------------
# Equation Solvers
# ----------------------------------------------------------------

# Solves a PQ-Equation: x² + px + q = 0    
def solve_pq(p, q):
    discriminant = (p / 2) ** 2 - q

    if discriminant < 0:
        return "No real roots (discriminant < 0)"
    elif discriminant == 0:
        x = -p / 2
        return f"x = {format_number(x)} (repeated root)"
    else:
        x1 = -p / 2 + math.sqrt(discriminant)
        x2 = -p / 2 - math.sqrt(discriminant)
        return f"x₁ = {format_number(x1)}\nx₂ = {format_number(x2)}"
    
# Solves a quadratic equation: ax² + bx + c = 0
def solve_quadratic(a, b, c):
    discriminant = b ** 2 - 4 * a * c
    if discriminant < 0:
        return "No real solutions (discriminant < 0)"
    x1 = (-b + math.sqrt(discriminant)) / (2 * a)
    x2 = (-b - math.sqrt(discriminant)) / (2 * a)
    return f"x₁ = {format_number(x1)}\nx₂ = {format_number(x2)}"

# Solves an equation system using sympy.
def solve_equation(equation_str: str) -> str:
    try:
        # define x
        x = symbols('x')
        # Remove quotes if present
        equation_str = equation_str.strip('"\'')
        # Replace ^ and ² with **
        equation_str = equation_str.replace('^', '**').replace('²', '**2')
        # Replace 2x with 2*x for proper multiplication
        equation_str = re.sub(r'(\d)([xy])', r'\1*\2', equation_str)
        
        # Parse and solve the equation
        expr = sympify(equation_str)
        solutions = solve(expr, x)

        if not solutions:
            return "No valid solutions found!"
        
        # Format solutions
        formatted_solutions = []
        for i, sol in enumerate(solutions, start=1):
            sol = complex(sol.evalf())  # Convert to Complex for better handling
            if abs(sol.imag) < 1e-10:  # Real number
                formatted_solutions.append(f"x{i} = {format_number(sol.real)}")
            else:  # Complex number
                formatted_solutions.append(f"x{i} = {format_number(sol.real)} + {format_number(sol.imag)}i")

        return "\n".join(formatted_solutions)

    except sympy.SympifyError as e:
        logging.error(f"Error parsing equation: {equation_str} - {str(e)}")
        return f"Invalid equation format: {str(e)}"
    except Exception as e:
        logging.error(f"Error solving equation: {equation_str} - {str(e)}")
        return f"An error occurred while solving: {str(e)}"

# Solves a system of equations using sympy
def solve_equation_system(equations):
    try:
        # Parse the equations
        parsed_equations = []
        for eq in equations:
            # Replace '^' with '**' for exponentiation
            eq = eq.replace('^', '**')
            # Replace 2x with 2*x for proper multiplication
            eq = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', eq)
            # Convert 'x + y = 5' to 'x + y - 5'
            if '=' in eq:
                lhs, rhs = eq.split('=')
                eq = f"({lhs}) - ({rhs})"
            parsed_equations.append(sympify(eq))

        # Define variables (x, y, z, etc.)
        variables = symbols(' '.join(set(re.findall(r'[a-zA-Z]', ' '.join(equations)))))

        # Solve the system of equations
        solutions = solve(parsed_equations, variables)

        if not solutions:
            return "No solution found!"

        if isinstance(solutions, dict):
            return "\n".join([f"{var} = {format_number(float(val))}" for var, val in solutions.items()])
        else:
            return "\n".join([
                f"Solution {i+1}: " + ", ".join([f"{var} = {format_number(float(sol[j]))}" for j, var in enumerate(variables)])
                for i, sol in enumerate(solutions)
            ])
    except Exception as e:
        logging.error(f"Error solving equation system: {equations} - {str(e)}")
        return f"Error solving equation system: {str(e)}"
    
# For safety, only allow specific math functions. Gets used in is_safe_expression and calculate_with_timeout.

# Safe math functions for the calculator
SAFE_FUNCTIONS = {
    # Basic math operations
    'sqrt': math.sqrt,
    'cbrt': lambda x: x**(1/3),  # Cubic root
    'root4': lambda x: x**(1/4),  # Fourth root
    'ln': math.log, 
    'log': math.log10,
    'log2': math.log2,
        
    # Trigonometric functions (in radians)
    'sin': math.sin, 
    'cos': math.cos, 
    'tan': math.tan,
    'asin': math.asin, 
    'acos': math.acos, 
    'atan': math.atan,
        
    # Hyperbolic functions
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
        
    # Other math functions
    'exp': math.exp, 
    'pow': math.pow,
    'factorial': math.factorial,
    'abs': abs,
    'floor': math.floor,
    'ceil': math.ceil,
    'round': round,
        
    # Constants
    'pi': math.pi, 
    'e': math.e,
    'tau': math.tau,
    'inf': math.inf,
    
    # Summation and product functions
    'sum': lambda expr, start, end: sum(sympify(expr).subs('n', i) for i in range(start, end + 1)),
    'prod': lambda expr, start, end: math.prod(sympify(expr).subs('n', i) for i in range(start, end + 1)),
    
    # Unit conversions
    
    # Temperature
    'c_to_f': lambda x: x * 9/5 + 32,
    'f_to_c': lambda x: (x - 32) * 5/9,
    'c_to_k': lambda x: x + 273.15,
    'k_to_c': lambda x: x - 273.15,
    'f_to_k': lambda x: (x - 32) * 5/9 + 273.15,
    'k_to_f': lambda x: (x - 273.15) * 9/5 + 32,

    # Distance / Length
    'km_to_mi': lambda x: x * 0.621371,
    'mi_to_km': lambda x: x / 0.621371,
    'm_to_ft': lambda x: x * 3.28084,
    'ft_to_m': lambda x: x / 3.28084,
    'cm_to_in': lambda x: x / 2.54,
    'in_to_cm': lambda x: x * 2.54,
    'mm_to_in': lambda x: x / 25.4,
    'in_to_mm': lambda x: x * 25.4,
    'km_to_m': lambda x: x * 1000,
    'm_to_km': lambda x: x / 1000,
    'cm_to_m': lambda x: x / 100,
    'm_to_cm': lambda x: x * 100,
    'mm_to_cm': lambda x: x / 10,
    'cm_to_mm': lambda x: x * 10,

    # Weight / Mass
    'kg_to_lb': lambda x: x * 2.20462,
    'lb_to_kg': lambda x: x / 2.20462,
    'g_to_oz': lambda x: x * 0.035274,
    'oz_to_g': lambda x: x / 0.035274,
    'kg_to_g': lambda x: x * 1000,
    'g_to_kg': lambda x: x / 1000,
    'lb_to_oz': lambda x: x * 16,
    'oz_to_lb': lambda x: x / 16,

    # Area
    'm2_to_ft2': lambda x: x * 10.7639,
    'ft2_to_m2': lambda x: x / 10.7639,
    'km2_to_mi2': lambda x: x * 0.386102,
    'mi2_to_km2': lambda x: x / 0.386102,
    'ha_to_acre': lambda x: x * 2.47105,
    'acre_to_ha': lambda x: x / 2.47105,
    'm2_to_cm2': lambda x: x * 10000,
    'cm2_to_m2': lambda x: x / 10000,

    # Volume
    'l_to_ml': lambda x: x * 1000,
    'ml_to_l': lambda x: x / 1000,
    'l_to_gal': lambda x: x * 0.264172,
    'gal_to_l': lambda x: x / 0.264172,
    'm3_to_l': lambda x: x * 1000,
    'l_to_m3': lambda x: x / 1000,
    'ft3_to_m3': lambda x: x / 35.3147,
    'm3_to_ft3': lambda x: x * 35.3147,

    # Speed
    'kmh_to_ms': lambda x: x / 3.6,
    'ms_to_kmh': lambda x: x * 3.6,
    'kmh_to_mph': lambda x: x * 0.621371,
    'mph_to_kmh': lambda x: x / 0.621371,
    'ms_to_mph': lambda x: x * 2.23694,
    'mph_to_ms': lambda x: x / 2.23694,
    'knots_to_kmh': lambda x: x * 1.852,
    'kmh_to_knots': lambda x: x / 1.852,
    'knots_to_mph': lambda x: x * 1.15078,
    'mph_to_knots': lambda x: x / 1.15078,

    # Pressure
    'pa_to_bar': lambda x: x / 100000,
    'bar_to_pa': lambda x: x * 100000,
    'pa_to_psi': lambda x: x / 6894.76,
    'psi_to_pa': lambda x: x * 6894.76,
    'bar_to_psi': lambda x: x * 14.5038,
    'psi_to_bar': lambda x: x / 14.5038,

    # Time
    's_to_min': lambda x: x / 60,
    'min_to_s': lambda x: x * 60,
    'min_to_h': lambda x: x / 60,
    'h_to_min': lambda x: x * 60,
    'h_to_d': lambda x: x / 24,
    'd_to_h': lambda x: x * 24,
    'd_to_y': lambda x: x / 365.25,
    'y_to_d': lambda x: x * 365.25,
    'min_to_d': lambda x: x / (60*24),
    'd_to_min': lambda x: x * 60 * 24,

    # Energy
    'j_to_kj': lambda x: x / 1000,
    'kj_to_j': lambda x: x * 1000,
    'j_to_cal': lambda x: x / 4.184,
    'cal_to_j': lambda x: x * 4.184,
    'wh_to_kwh': lambda x: x / 1000,
    'kwh_to_wh': lambda x: x * 1000,
    'v_to_mv': lambda x: x * 1000,
    'mv_to_v': lambda x: x / 1000,
    'a_to_ma': lambda x: x * 1000,
    'ma_to_a': lambda x: x / 1000,
    'ohm_to_kohm': lambda x: x / 1000,
    'kohm_to_ohm': lambda x: x * 1000,
    'w_to_kw': lambda x: x / 1000,
    'kw_to_w': lambda x: x * 1000,

    # Data
    'b_to_kb': lambda x: x / 1024,
    'kb_to_b': lambda x: x * 1024,
    'kb_to_mb': lambda x: x / 1024,
    'mb_to_kb': lambda x: x * 1024,
    'mb_to_gb': lambda x: x / 1024,
    'gb_to_mb': lambda x: x * 1024,
    'gb_to_tb': lambda x: x / 1024,
    'tb_to_gb': lambda x: x * 1024,
    
    # Decimal-based data units
    'b_to_kB': lambda x: x / 1000,
    'kB_to_b': lambda x: x * 1000,
    'kB_to_MB': lambda x: x / 1000,
    'MB_to_kB': lambda x: x * 1000,
    'MB_to_GB': lambda x: x / 1000,
    'GB_to_MB': lambda x: x * 1000,
    'GB_to_TB': lambda x: x / 1000,
    'TB_to_GB': lambda x: x * 1000,

    # SymPy functions
    'solve': solve,

    # Additional safe functions
    'solve': solve_equation,
    'pq': lambda p, q: solve_pq(p, q),
    'quad': lambda a, b, c: solve_quadratic(a, b, c),
    'solve_system': solve_equation_system,
    'deg': math.degrees,
    'rad': math.radians,
    'gamma': math.gamma,
    'erf': math.erf,
    'comb': math.comb,
    'perm': math.perm,
    'mod': lambda a, b: a % b,

}

# Custom calculator exception
class CalculatorError(Exception):
    pass

# Formats error messages user-friendly
def format_error(error):
    error_mapping = {
        ZeroDivisionError: "Cannot divide by zero",
        OverflowError: "Value exceeds allowed range",
        ValueError: "Invalid input",
        SyntaxError: "Invalid expression syntax",
        CalculatorError: str(error),
        sympy.SympifyError: "Invalid mathematical expression"
    }
    return error_mapping.get(type(error), str(error))

# ----------------------------------------------------------------
# Main handler for !calc command
# ----------------------------------------------------------------

async def handle_calc_command(client, message, user_message):
    logging.debug(f"Calculator command received: {user_message}")  # Debug-Log
    try:
        expression = user_message[6:].strip()  # Remove '!calc ' prefix
        logging.debug(f"Parsed expression: {expression}")  # Debug-Log
        
        if not expression:
            logging.debug("Empty expression, sending help message")  # Debug-Log
            await send_help_message(message)
            return " ⚠️ You need to provide an expression to calculate."

        result = await process_calculation(message, expression)
        if result is not None:
            await send_calculation_result(message, expression, result)
            
        if result is None:
            return "❌ Calculation could not be completed."
            
    except Exception as e:
        logging.error(f"Calculator error: {str(e)}", exc_info=True)  # Detailed error log
        return f"❌ Error: {str(e)}"

# Processes the calculation and returns the result
async def process_calculation(message, expression):
    # Processes the calculation and returns the result
    calc_start = time.time()

    # Check for previous result
    if 'ans' in expression:
        if message.author.id not in LAST_RESULT:
            await message.channel.send("❌ No previous calculation found. Cannot use 'ans'.")
            return None
        expression = expression.replace('ans', str(LAST_RESULT[message.author.id]))

    # Safety checks
    is_safe, error_msg = is_safe_expression(expression)
    if not is_safe:
        await message.channel.send(f"❌ {error_msg}")
        return None

    # Replace special characters
    expression = replace_special_characters(expression)

    # Check if the expression contains a solve function
    try:
        if expression.startswith("solve(") and expression.endswith(")"):
            # Extract the equation inside solve()
            equation = expression[6:-1].strip()
            result = solve_equation(equation)
        else:
            # Calculate with timeout
            result = await calculate_with_timeout(expression)

        LAST_RESULT[message.author.id] = result
        
        calc_duration = time.time() - calc_start
        logging.debug(f"Calculation processed in {calc_duration:.2f} seconds.")
        
        return result
    except Exception as e:
        error_msg = format_error(e)
        await message.channel.send(f"❌ {error_msg}")
        logging.error(f"Calculation error for {message.author}: {error_msg}")
        return None
    
# Sends the calculation result as an embed
async def send_calculation_result(message, original_expression, result):
    if isinstance(result, (int, float, str)):
        formatted_result = format_number(result)
    else:
        formatted_result = str(result)
    
    embed = discord.Embed(
        title="🔢 Calculator",
        color=discord.Color.blue()
    )
    embed.add_field(name="Expression", value=f"**{original_expression}**", inline=False)
    embed.add_field(name="Result", value=f"**{formatted_result}**", inline=False)
    embed.set_footer(text="💡 Tip: Use 'ans' in your next calculation to use the last result!!")

    await message.channel.send(embed=embed)
    logging.debug(f"Calculation performed for {message.author}: {original_expression} = {result}")

# Sends the help message for the calculator
async def send_help_message(message):
    help_msg = (
        "📝 **How to use the calculator:**\n\n"
        "`!calc <expression>`\n\n"
        "**Basic Operations:**\n"
        "  - Addition (+), Subtraction (-)\n"
        "  - Multiplication (×, *), Division (÷, /)\n"
        "  - Powers (^, x², x³, x⁴, x⁵, x⁶, x⁷, x⁸, x⁹)\n"
        "  - Square Root (√), Cubic Root (∛), Fourth Root (∜)\n"
        "\n**Mathematical Functions:**\n"
        "  - Logarithms: ln(x), log(x), log2(x)\n"
        "  - Trigonometry: sin(x), cos(x), tan(x)\n"
        "  - Inverse Trig: asin(x), acos(x), atan(x)\n"
        "  - Hyperbolic: sinh(x), cosh(x), tanh(x)\n"
        "\n**Other Functions:**\n"
        "  - exp(x), abs(x), factorial(x)\n"
        "  - floor(x), ceil(x), round(x)\n"
        "\n**Constants:**\n"
        "  - π (pi), e, τ (tau), ∞ (inf)\n"
        "\n **Special Features:**\n"
        "  - Previous result: ans\n"
        "  - Equation solving: solve(equation)\n"
        "  - PQ formula: pq(p,q)\n"
        "  - Quadratic: quad(a,b,c)\n"
        "  - Equation systems: solve_system(['eq1', 'eq2', ...])\n"
        "  - Summation: sum(expr, start, end)\n"
        "  - Product: prod(expr, start, end)\n"
        "  - Unit conversion: c_to_f(x), km_to_mi(x)\n"
        "\n**Examples:**\n"
        "• `!calc 2 + 2`\n"
        "• `!calc sin(45) + cos(30)`\n"
        "• `!calc √(16) + ∛(27)`\n"
        "• `!calc 2³ + π`\n"
        "• `!calc solve(x^2 + 2x + 1)`\n"
        "• `!calc ans + 5`\n"
        "• `!calc solve_system(['x + y = 5', 'x - y = 1'])`\n"
        "• `!calc sum('n**2', 1, 5)`\n"
        "• `!calc c_to_f(20)`"
    )
    await message.channel.send(help_msg)

# Replaces special mathematical characters with their python equivalents
def replace_special_characters(expression):
    replacements = {
        # Exponents
        '²': '**2', '³': '**3', '⁴': '**4',
        '⁵': '**5', '⁶': '**6', '⁷': '**7',
        '⁸': '**8', '⁹': '**9',

        # Mathematical symbols
        '^': '**', '×': '*', '·': '*', '÷': '/',

        # Roots
        '√': 'sqrt', '∛': 'cbrt', '∜': 'root4',

        # Greek letters and symbols
        'π': 'pi', 'τ': 'tau', '∞': 'inf', 'ℯ': 'e',

        # Other symbols
        '±': ' + [-]', '∓': ' - [+]',
        '∑': 'sum', '∏': 'prod', '∆': 'delta'
    }
    
    result = expression
    for old, new in replacements.items():
        result = result.replace(old, new)
        
    # Convert degrees to radians for trig functions
    if any(func in result for func in ['sin(', 'cos(', 'tan(']):
        result = re.sub(r'(sin|cos|tan)\((.+?)\)', r'\1((\2) * pi / 180)', result)
    
    return result

# Formats a number to a user-friendly string
#    - Converts very small numbers near 0 to 0
#    - Converts integers to whole numbers
#    - Rounds decimal numbers to 4 decimal places
#    - Removes unnecessary trailing zeros
#    - Changes very large or small numbers to scientific notation
#    - Handles special cases like π (pi), e, and τ (tau)
def format_number(value: float | str) -> str:
    try:
        # Convert to float if string
        if isinstance(value, str):
            if '/' in value:  # Handle fractions like "1/3"
                num, denom = map(float, value.split('/'))
                value = num / denom
            else:
                value = float(value)
        
        num = float(value)
        
        # If numbers are close to 0 (within 1e-10), return 0
        if abs(num) < 1e-10:
            return "0"
            
        # If number is an integer (e.g., 8.0), return as whole number (e.g., 8)
        if abs(num - round(num)) < 1e-10:
            return str(int(round(num)))
            
        # Handle special cases for mathematical constants
        if abs(abs(num) - math.pi) < 1e-10:
            return "π"  # Return π symbol
        if abs(abs(num) - math.e) < 1e-10:
            return "e"  # Return e symbol
        if abs(abs(num) - math.tau) < 1e-10:
            return "τ"  # Return τ symbol
            
        # Scientific notation for very small or large numbers
        abs_num = abs(num)
        if abs_num < 0.0001 or abs_num > 10000:
            return f"{num:.2e}"
            
        # Round to 4 decimal places
        rounded = round(num, 4)
        str_num = f"{rounded}"
        
        # Remove trailing zeros and decimal point
        if '.' in str_num:
            str_num = str_num.rstrip('0').rstrip('.')
            
        return str_num
        
    except (ValueError, TypeError, ZeroDivisionError):
        return str(value)