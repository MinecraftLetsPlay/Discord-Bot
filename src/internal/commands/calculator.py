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
        return False, "Invalid keywords detected"
        
    if expression.count('(') != expression.count(')'):
        return False, "Unbalanced parentheses"
        
    return True, ""

async def calculate_with_timeout(expression):
    """Executes calculation with timeout"""
    try:
        return await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: sympify(expression, locals=SAFE_FUNCTIONS)
            ),
            timeout=CALCULATION_TIMEOUT
        )
    except asyncio.TimeoutError:
        raise CalculatorError("Calculation timed out")
    
def solve_pq(p, q):
    """Löst eine PQ-Formel-Gleichung: x² + px + q = 0"""
    discriminant = (p / 2) ** 2 - q

    if discriminant < 0:
        return "Keine reellen Lösungen (diskriminante < 0)"
    elif discriminant == 0:
        x = -p / 2
        return f"x = {format_number(x)} (doppelte Lösung)"
    else:
        x1 = -p / 2 + math.sqrt(discriminant)
        x2 = -p / 2 - math.sqrt(discriminant)
        return f"x₁ = {format_number(x1)}\nx₂ = {format_number(x2)}"

def solve_quadratic(a, b, c):
    """Löst eine quadratische Gleichung: ax² + bx + c = 0"""
    discriminant = b ** 2 - 4 * a * c
    if discriminant < 0:
        return "Keine reellen Lösungen"
    x1 = (-b + math.sqrt(discriminant)) / (2 * a)
    x2 = (-b - math.sqrt(discriminant)) / (2 * a)
    return f"x₁ = {format_number(x1)}\nx₂ = {format_number(x2)}"

def solve_equation(equation_str: str) -> str:
    """
    Löst eine mathematische Gleichung mit SymPy.
    """
    try:
        x = symbols('x')
        equation_str = equation_str.replace('^', '**')  # Ersetze ^ mit ** für Potenzen
        expr = sympify(equation_str)
        solutions = solve(expr, x)

        if not solutions:
            return "Keine Lösungen gefunden!"
        
        # Formatierung der Lösungen
        formatted_solutions = []
        for i, sol in enumerate(solutions, start=1):
            sol = sol.evalf()  # Wert berechnen
            if sol.is_real:
                formatted_solutions.append(f"x{i} = {format_number(float(sol))}")  # float() hinzugefügt
            else:
                formatted_solutions.append(f"x{i} = {sol}")

        return "\n".join(formatted_solutions)

    except sympy.SympifyError as e:
        logging.error(f"Fehler beim Parsen der Gleichung: {equation_str} - {str(e)}")
        return "Ungültiges Gleichungsformat"
    except Exception as e:
        logging.error(f"Fehler beim Lösen der Gleichung: {equation_str} - {str(e)}")
        return f"Fehler beim Lösen: {str(e)}"

def solve_equation_system(equations):
    """Löst ein Gleichungssystem mit SymPy"""
    try:
        x, y = symbols('x y')
        equations = [sympify(eq) for eq in equations]
        solutions = solve(equations, (x, y))

        if not solutions:
            return "Keine Lösungen gefunden!"
        
        if isinstance(solutions, dict):
            return "\n".join([f"{var} = {format_number(float(val))}" for var, val in solutions.items()])
        else:
            return "\n".join([
                f"Lösung {i+1}: x = {format_number(float(sol[0]))}, y = {format_number(float(sol[1]))}" 
                for i, sol in enumerate(solutions)
            ])
    except Exception as e:
        return f"Fehler beim Lösen des Gleichungssystems: {str(e)}"

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
        OverflowError: "Number too large",
        ValueError: "Invalid input",
        SyntaxError: "Invalid expression syntax",
        CalculatorError: str(error),
        sympy.core.sympify.SympifyError: "Invalid mathematical expression"
    }
    return error_mapping.get(type(error), str(error))



async def handle_calc_command(message, user_message):
    """Handles the calculator command"""
    try:
        expression = user_message[6:].strip()  # Remove '!calc ' prefix
        
        if not expression:
            await send_help_message(message)
            return

        result = await process_calculation(message, expression)
        if result is not None:
            await send_calculation_result(message, expression, result)
            
    except ZeroDivisionError:
        await message.channel.send("❌ Cannot divide by zero!")
    except (SyntaxError, ValueError, NameError):
        await message.channel.send("❌ Invalid expression. Type `!calc` for help.")
        logging.warning(f"Invalid expression from {message.author}: {expression}")
    except Exception as e:
        await message.channel.send(f"❌ Error: {str(e)}")
        logging.error(f"Calculation error for {message.author}: {str(e)}")

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
    embed.set_footer(text="💡 Tip: Use 'ans' in your next calculation to use this result!")

    await message.channel.send(embed=embed)
    logging.info(f"Calculation performed for {message.author}: {original_expression} = {result}")

async def send_help_message(message):
    """Sends the help message for the calculator"""
    help_msg = (
        "📝 **Calculator Usage:**\n\n"
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
        "  - Equation systems: solve_system([eq1, eq2])\n"
        "  - Summation: sum(expr, start, end)\n"
        "  - Product: prod(expr, start, end)\n"
        "  - Unit conversion: c_to_f(x), km_to_mi(x)\n"
        "\n**Examples:**\n"
        "• `!calc 2 + 2`\n"
        "• `!calc sin(45) + cos(30)`\n"
        "• `!calc √(16) + ∛(27)`\n"
        "• `!calc 2³ + π`\n"
        "• `!calc solve(x^2 + 2x + 1)`\n"
        "• `!calc ans + 5`"
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
    
    return result  # Dies war am falschen Ort

def format_number(value: str) -> str:
    """
    Formatiert Zahlen-Strings für bessere Lesbarkeit:
    - Entfernt unnötige Nachkommastellen
    - Konvertiert wissenschaftliche Notation wenn sinnvoll
    """
    try:
        # Wenn es keine Zahl ist, original zurückgeben
        if not isinstance(value, (str, int, float)):
            return str(value)
            
        # String in Float konvertieren
        num = float(str(value).strip())
        
        # Ganzzahl check
        if num.is_integer():
            return str(int(num))
            
        # Wissenschaftliche Notation für sehr große/kleine Zahlen
        abs_num = abs(num)
        if abs_num < 0.0001 or abs_num > 10000:
            return f"{num:.2e}"
            
        # Entferne unnötige Nullen am Ende
        str_num = f"{num:.10f}".rstrip('0').rstrip('.')
        
        # Wenn mehr als 4 Nachkommastellen, auf 4 runden
        if '.' in str_num and len(str_num.split('.')[1]) > 4:
            return f"{num:.4f}".rstrip('0').rstrip('.')
            
        return str_num
        
    except (ValueError, TypeError):
        return str(value)
        

        
    return result