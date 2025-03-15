import discord
import math
import re
import logging
import sympy
from sympy import solve, symbols, parse_expr

# Store last result for 'ans' functionality
LAST_RESULT = {}

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
    'inf': math.inf
}

# Add additional functions to SAFE_FUNCTIONS
SAFE_FUNCTIONS.update({
    'cbrt': lambda x: x**(1/3),  # Cubic root
    'root4': lambda x: x**(1/4),  # Fourth root
    'solve': lambda eq: solve_equation(eq),
    'pq': lambda p, q: solve_pq(p, q),
    'quad': lambda a, b, c: solve_quadratic(a, b, c)
})

def solve_pq(p, q):
    """Solves a PQ equation: x² + px + q = 0"""
    if q > 0:
        return "No real solutions (q must be ≤ 0 for real solutions)"
        
    discriminant = (p/2)**2 - q
    
    if discriminant < 0:
        return "No real solutions (discriminant < 0)"
    elif discriminant == 0:
        x = -p/2
        return f"x = {x:.4g} (double root)"
    else:
        x1 = -p/2 + math.sqrt(discriminant)
        x2 = -p/2 - math.sqrt(discriminant)
        return f"x₁ = {x1:.4g}\nx₂ = {x2:.4g}"

def solve_quadratic(a, b, c):
    """Solves a quadratic equation: ax² + bx + c = 0"""
    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        return "No real solutions"
    x1 = (-b + math.sqrt(discriminant))/(2*a)
    x2 = (-b - math.sqrt(discriminant))/(2*a)
    return f"x₁ = {x1:.4g}\nx₂ = {x2:.4g}"

def solve_equation(equation_str):
    """Solves a general equation using sympy"""
    x = symbols('x')
    try:
        equation = parse_expr(equation_str)
        solutions = solve(equation, x)
        if not solutions:
            return "No solutions found!"
        return "\n".join([f"x{i+1 if len(solutions)>1 else ''} = {sol}" for i, sol in enumerate(solutions)])
    except Exception as e:
        return f"Error solving equation: {str(e)}"

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
    if 'ans' in expression:
        if message.author.id not in LAST_RESULT:
            await message.channel.send("❌ No previous calculation found. Cannot use 'ans'.")
            return None
        expression = expression.replace('ans', str(LAST_RESULT[message.author.id]))

    expression = replace_special_characters(expression)
    
    if re.search(r'[^0-9+\-*/()., \w]', expression):
        logging.warning(f"Invalid characters in expression: {expression}")
        await message.channel.send("❌ Invalid characters detected!")
        return None

    result = eval(expression, {"__builtins__": None}, SAFE_FUNCTIONS)
    LAST_RESULT[message.author.id] = result
    return result

async def send_calculation_result(message, original_expression, result):
    """Sends the calculation result as an embed"""
    formatted_result = f"{result:.10g}" if isinstance(result, float) else str(result)
    
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
        "📝 **Calculator Usage:**\n"
        "!calc <expression>\n\n"
        "**Available Functions:**\n"
        "• Basic Operations:\n"
        "  - Addition (+), Subtraction (-)\n"
        "  - Multiplication (×, *), Division (÷, /)\n"
        "  - Powers (^, ², ³, ⁴, ⁵, ⁶, ⁷, ⁸, ⁹)\n"
        "  - Square Root (√), Cubic Root (∛), Fourth Root (∜)\n"
        "\n• Mathematical Functions:\n"
        "  - Logarithms: ln(x), log(x), log2(x)\n"
        "  - Trigonometry: sin(x), cos(x), tan(x)\n"
        "  - Inverse Trig: asin(x), acos(x), atan(x)\n"
        "  - Hyperbolic: sinh(x), cosh(x), tanh(x)\n"
        "\n• Other Functions:\n"
        "  - exp(x), abs(x), factorial(x)\n"
        "  - floor(x), ceil(x), round(x)\n"
        "\n• Constants:\n"
        "  - π (pi), e, τ (tau), ∞ (inf)\n"
        "\n• Special Features:\n"
        "  - Previous result: ans\n"
        "  - Equation solving: solve(equation)\n"
        "  - PQ formula: pq(p,q)\n"
        "  - Quadratic: quad(a,b,c)\n"
        "\n**Examples:**\n"
        "• !calc 2 + 2\n"
        "• !calc sin(45) + cos(30)\n"
        "• !calc √(16) + ∛(27)\n"
        "• !calc 2³ + π\n"
        "• !calc solve(x^2 + 2x + 1)\n"
        "• !calc ans + 5"
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