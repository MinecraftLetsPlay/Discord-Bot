import discord
import math
import re
import logging
import sympy
import asyncio
from sympy import solve, symbols, parse_expr, sympify

# Store last result for 'ans' functionality
LAST_RESULT = {}

# Sicherheitskonfiguration
MAX_EXPRESSION_LENGTH = 500
CALCULATION_TIMEOUT = 5  # Sekunden

def is_safe_expression(expression):
    """Checks if an expression is safe to evaluate"""
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return False, "Expression too long (max 500 characters)"
        
    dangerous_keywords = ['import', 'eval', 'exec', 'open', '__', 'javascript:', 'js:', 'file:', 'ftp:', 'http:', 'https:', 'data:', r"\\x[0-9a-fA-F]{2}"]
    if any(keyword in expression.lower() for keyword in dangerous_keywords):
        return False, "Forbidden keywords detected"
        
    if expression.count('(') != expression.count(')'):
        return False, "Unbalanced parentheses"
        
    return True, ""

async def calculate_with_timeout(expression):
    """Executes calculation with timeout"""
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: sympify(expression, locals=SAFE_FUNCTIONS)
            ),
            timeout=CALCULATION_TIMEOUT
        )
        
        # Formatiere das Ergebnis
        if isinstance(result, (int, float, sympy.core.numbers.Number)):
            return format_number(float(result))
        return str(result)
        
    except asyncio.TimeoutError:
        raise CalculatorError("Calculation timed out")
    
def solve_pq(p, q):
    """Solves a PQ-Equation: x² + px + q = 0"""
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

def solve_quadratic(a, b, c):
    """Solves a quadratic equation: ax² + bx + c = 0"""
    discriminant = b ** 2 - 4 * a * c
    if discriminant < 0:
        return "No real solutions (discriminant < 0)"
    x1 = (-b + math.sqrt(discriminant)) / (2 * a)
    x2 = (-b - math.sqrt(discriminant)) / (2 * a)
    return f"x₁ = {format_number(x1)}\nx₂ = {format_number(x2)}"

def solve_equation(equation_str: str) -> str:
    """Solves an equation system using sympy."""
    try:
        x = symbols('x')
        # Entferne Anführungszeichen, falls vorhanden
        equation_str = equation_str.strip('"\'')
        # Ersetze ^ und ² mit **
        equation_str = equation_str.replace('^', '**').replace('²', '**2')
        # Ersetze 2x mit 2*x für korrekte Multiplikation
        equation_str = re.sub(r'(\d)([xy])', r'\1*\2', equation_str)
        
        expr = sympify(equation_str)
        solutions = solve(expr, x)

        if not solutions:
            return "No valid solutions found!"
        
        formatted_solutions = []
        for i, sol in enumerate(solutions, start=1):
            sol = complex(sol.evalf())  # Konvertiere zu Complex für bessere Verarbeitung
            if abs(sol.imag) < 1e-10:  # Reelle Zahl
                formatted_solutions.append(f"x{i} = {format_number(sol.real)}")
            else:  # Komplexe Zahl
                formatted_solutions.append(f"x{i} = {format_number(sol.real)} + {format_number(sol.imag)}i")

        return "\n".join(formatted_solutions)

    except sympy.SympifyError as e:
        logging.error(f"Error parsing equation: {equation_str} - {str(e)}")
        return f"Invalid equation format: {str(e)}"
    except Exception as e:
        logging.error(f"Error solving equation: {equation_str} - {str(e)}")
        return f"An error occured while solving: {str(e)}"

def solve_equation_system(equations):
    """Solves a system of equations using SymPy"""
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

# Safe math functions for the calculator
SAFE_FUNCTIONS = {
    # Basic math operations
    'sqrt': math.sqrt, 
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
    'c_to_f': lambda x: x * 9/5 + 32,
    'f_to_c': lambda x: (x - 32) * 5/9,
    'km_to_mi': lambda x: x * 0.621371,
    'mi_to_km': lambda x: x / 0.621371,

    # SymPy functions
    'solve': solve,  # Hinzufügen von solve
}

# Add additional functions to SAFE_FUNCTIONS
SAFE_FUNCTIONS.update({
    'cbrt': lambda x: x**(1/3),  # Cubic root
    'root4': lambda x: x**(1/4),  # Fourth root
    'solve': solve_equation,
    'pq': lambda p, q: solve_pq(p, q),
    'quad': lambda a, b, c: solve_quadratic(a, b, c),
    'solve_system': solve_equation_system
})

class CalculatorError(Exception):
    """Custom calculator exception"""
    pass

def format_error(error):
    """Formats error messages user-friendly"""
    error_mapping = {
        ZeroDivisionError: "Cannot divide by zero",
        OverflowError: "Value exceeds allowed range",
        ValueError: "Invalid input",
        SyntaxError: "Invalid expression syntax",
        CalculatorError: str(error),
        sympy.SympifyError: "Invalid mathematical expression"
    }
    return error_mapping.get(type(error), str(error))



async def handle_calc_command(client, message, user_message):
    """Handles the calculator command"""
    logging.debug(f"Calculator command received: {user_message}")  # Debug-Log
    try:
        expression = user_message[6:].strip()  # Remove '!calc ' prefix
        logging.debug(f"Parsed expression: {expression}")  # Debug-Log
        
        if not expression:
            logging.debug("Empty expression, sending help message")  # Debug-Log
            await send_help_message(message)
            return

        result = await process_calculation(message, expression)
        if result is not None:
            await send_calculation_result(message, expression, result)
            
    except Exception as e:
        logging.error(f"Calculator error: {str(e)}", exc_info=True)  # Detailed error log
        await message.channel.send(f"❌ Error: {str(e)}")

async def process_calculation(message, expression):
    """Processes the calculation and returns the result"""
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

    try:
        # Check if the expression contains a solve function
        if expression.startswith("solve(") and expression.endswith(")"):
            # Extract the equation inside solve()
            equation = expression[6:-1].strip()
            result = solve_equation(equation)
        else:
            # Calculate with timeout
            result = await calculate_with_timeout(expression)

        LAST_RESULT[message.author.id] = result
        return result
    except Exception as e:
        error_msg = format_error(e)
        await message.channel.send(f"❌ {error_msg}")
        logging.error(f"Calculation error for {message.author}: {error_msg}")
        return None

async def send_calculation_result(message, original_expression, result):
    """Sends the calculation result as an embed"""
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
    logging.info(f"Calculation performed for {message.author}: {original_expression} = {result}")

async def send_help_message(message):
    """Sends the help message for the calculator"""
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

def replace_special_characters(expression):
    """Replaces special mathematical characters with their python equivalents"""
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

def format_number(value: float | str) -> str:
    """
    Formats a number to a user-friendly string
    - Converts very small numbers near 0 to 0
    - Converts integers to whole numbers
    - Rounds decimal numbers to 4 decimal places
    - Removes unnecessary trailing zeros
    """
    try:
        # Konvert to float if string
        if isinstance(value, str):
            if '/' in value:
                num, denom = map(float, value.split('/'))
                value = num / denom
            else:
                value = float(value)
        
        num = float(value)
        
        # If numbers are close to 0 (within 1e-10), return 0
        if abs(num) < 1e-10:
            return "0"
            
        # If number is an integer (8.0), return as whole number (8)
        if abs(num - round(num)) < 1e-10:
            return str(int(round(num)))
            
        # Convert PI to 3.1416
        if abs(abs(num) - math.pi) < 1e-10:
            return "3.1416"
            
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