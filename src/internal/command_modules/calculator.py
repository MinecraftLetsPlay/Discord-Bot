import discord
import math
import re
import logging
import sympy
import asyncio
import time
from sympy import solve, symbols, parse_expr, sympify, Number
from typing import Tuple, Optional, Dict, Any
from internal import rate_limiter

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: Calculator.py
# Description: A all around, text-based calculator capable of equation solving
# Security: Code injection prevention, input validation, timeout protection
# ================================================================

# ----------------------------------------------------------------
# CONSTANTS & SECURITY CONFIGURATION
# ----------------------------------------------------------------

# Expression validation
MAX_EXPRESSION_LENGTH = 500
CALCULATION_TIMEOUT = 5.0  # Seconds
MAX_VARIABLES_IN_EQUATION = 10
MAX_EQUATION_COMPLEXITY = 100  # Maximum number of operations

# Custom calculator exception
class CalculatorError(Exception):
    pass

# Raised when a security violation is detected
class SecurityError(CalculatorError):
    pass

# ----------------------------------------------------------------
# Component test function for calculator module
# ----------------------------------------------------------------

def component_test():
    status = "🟩"
    messages = ["Calculator module loaded."]
    
    return {"status": status, "msg": " | ".join(messages)}

# ----------------------------------------------------------------
# SECURITY & INPUT VALIDATION
# ----------------------------------------------------------------

# Store last result for 'ans' functionality
LAST_RESULT: Dict[int, Any] = {}

# Check expression complexity to prevent DoS
def check_expression_complexity(expression: str) -> Tuple[bool, str]:
    try:
        # Check nesting depth (parentheses, brackets, braces)
        max_depth = 0
        current_depth = 0
        for char in expression:
            if char in '([{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in ')]}':
                current_depth -= 1
        
        MAX_NESTING_DEPTH = 10
        if max_depth > MAX_NESTING_DEPTH:
            logging.warning(f"Expression nesting too deep: {max_depth} (max {MAX_NESTING_DEPTH})")
            return False, f"Expression nesting too deep (max {MAX_NESTING_DEPTH} levels)"
        
        # Count operations to prevent DoS
        operation_count = (
            expression.count('+') + expression.count('-') +
            expression.count('*') + expression.count('/') +
            expression.count('^') + expression.count('**') +
            expression.count('(') + expression.count('[')
        )
        
        MAX_OPERATIONS = 50
        if operation_count > MAX_OPERATIONS:
            logging.warning(f"Too many operations: {operation_count} (max {MAX_OPERATIONS})")
            return False, f"Expression too complex (max {MAX_OPERATIONS} operations)"
        
        return True, ""
    
    except Exception as e:
        logging.error(f"Error in check_expression_complexity: {str(e)}")
        return False, "Could not validate expression complexity"

# Validate variable names against whitelist
def validate_variable_names(expression: str) -> Tuple[bool, str]:
    try:
        # Extract all identifiers (variable/function names)
        # Pattern: word characters, but exclude numbers at start
        identifier_pattern = r'\b([a-zA-Z_]\w*)\b'
        found_identifiers = set(re.findall(identifier_pattern, expression))
        
        # Remove known safe identifiers
        safe_identifiers = set(SAFE_FUNCTIONS.keys()) | {'ans', 'x', 'y', 'z', 'n', 'i', 'j', 'k'}
        
        # Check for unknown identifiers
        unknown_identifiers = found_identifiers - safe_identifiers
        
        if unknown_identifiers:
            logging.warning(f"Unknown identifiers detected: {unknown_identifiers}")
            return False, f"Unknown identifiers: {', '.join(list(unknown_identifiers)[:3])}"
        
        return True, ""
    
    except Exception as e:
        logging.error(f"Error in validate_variable_names: {str(e)}")
        return False, "Could not validate variable names"

# Validate function calls against whitelist
def validate_function_calls(expression: str) -> Tuple[bool, str]:
    try:
        # Extract function calls: identifier followed by (
        function_pattern = r'([a-zA-Z_]\w*)\s*\('
        found_functions = set(re.findall(function_pattern, expression))
        
        # Get allowed functions from SAFE_FUNCTIONS
        allowed_functions = set(SAFE_FUNCTIONS.keys())
        
        # Check for disallowed functions
        disallowed = found_functions - allowed_functions
        
        if disallowed:
            logging.warning(f"Disallowed functions detected: {disallowed}")
            return False, f"Function(s) not allowed: {', '.join(list(disallowed)[:3])}"
        
        return True, ""
    
    except Exception as e:
        logging.error(f"Error in validate_function_calls: {str(e)}")
        return False, "Could not validate function calls"


# Replaces special characters with Python-compatible ones and check for invalid patterns
def is_safe_expression(expression: str) -> Tuple[bool, str]:
    if not expression or len(expression) == 0:
        return False, "Expression cannot be empty"
    
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return False, f"Expression too long (max {MAX_EXPRESSION_LENGTH} chars)"
    
    # Check for null bytes
    if '\x00' in expression:
        return False, "Expression contains null bytes"
    
    # Normalize whitespace and convert to lowercase for pattern matching
    normalized = ' '.join(expression.split()).lower()
    
    # ========== LAYER 1: BLACKLIST DANGEROUS PATTERNS ==========
    dangerous_patterns = [
        # Code execution
        r'\b__import__\b',
        r'\beval\b',
        r'\bexec\b',
        r'\bcompile\b',
        r'\bglobals\b',
        r'\blocals\b',
        r'\bvars\b',
        r'\bdir\b',
        r'\bgetattr\b',
        r'\bsetattr\b',
        r'\bhasattr\b',
        r'\bdelattr\b',
        
        # Module imports
        r'\bimport\s',
        r'\bfrom\s',
        
        # File/System operations
        r'\bopen\b',
        r'\bfile\b',
        r'\bos\.',
        r'\bsys\.',
        r'\bsubprocess\b',
        r'\bpathlib\b',
        
        # Object/Class manipulation
        r'__[a-z]+__',  # Dunder methods
        r'\.__bases__',
        r'\.__class__',
        r'\.__dict__',
        r'\.__code__',
        r'\.__globals__',
        
        # Dangerous builtins
        r'\bexecfile\b',
        r'\binput\b',
        r'\braw_input\b',
        r'\breload\b',
        
        # Lambda abuse
        r'lambda\s+.*:.*import',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, normalized):
            logging.warning(f"Dangerous pattern detected: {pattern}")
            return False, "Expression contains forbidden keywords or patterns"
    
    # Check for suspicious character sequences
    suspicious_sequences = [
        '\\\\',  # Escaped backslashes
        '\\x',   # Hex escapes
        '\\u',   # Unicode escapes
    ]
    
    for sequence in suspicious_sequences:
        if sequence in expression:
            logging.warning(f"Suspicious sequence detected: {sequence}")
            return False, "Expression contains suspicious escape sequences"
    
    # ========== LAYER 2: CHECK COMPLEXITY ==========
    is_valid, error_msg = check_expression_complexity(expression)
    if not is_valid:
        return False, error_msg
    
    # ========== LAYER 3: VALIDATE FUNCTION CALLS (WHITELIST) ==========
    is_valid, error_msg = validate_function_calls(expression)
    if not is_valid:
        return False, error_msg
    
    # ========== LAYER 4: VALIDATE VARIABLE NAMES (WHITELIST) ==========
    is_valid, error_msg = validate_variable_names(expression)
    if not is_valid:
        return False, error_msg
    
    # ========== LAYER 5: CHECK BALANCED BRACKETS ==========
    if expression.count('(') != expression.count(')'):
        return False, "Unbalanced parentheses"
    
    if expression.count('[') != expression.count(']'):
        return False, "Unbalanced brackets"
    
    if expression.count('{') != expression.count('}'):
        return False, "Unbalanced braces"
    
    return True, ""

# Calculate with timeout protection
async def calculate_with_timeout(expression: str) -> str:
    try:
        # Run calculation in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: sympify(expression, locals=SAFE_FUNCTIONS)
            ),
            timeout=CALCULATION_TIMEOUT
        )
        
        # Format the result
        try:
            if isinstance(result, (int, float, Number)):
                return format_number(float(result))
            return str(result)
        except (ValueError, TypeError) as e:
            logging.error(f"Error formatting result: {str(e)}")
            return str(result)
        
    # Error handling
    except asyncio.TimeoutError:
        logging.warning(f"Calculation timeout for expression: {expression[:50]}")
        raise CalculatorError(f"Calculation timed out (exceeded {CALCULATION_TIMEOUT}s)")
    except ZeroDivisionError:
        logging.warning(f"Zero division in expression: {expression[:50]}")
        raise CalculatorError("Cannot divide by zero")
    except sympy.SympifyError as e:
        logging.warning(f"Sympy parsing error: {str(e)}")
        raise CalculatorError(f"Invalid mathematical expression: {str(e)}")
    except ValueError as e:
        logging.warning(f"Value error in calculation: {str(e)}")
        raise CalculatorError(f"Invalid value: {str(e)}")
    except TypeError as e:
        logging.warning(f"Type error in calculation: {str(e)}")
        raise CalculatorError(f"Invalid operation: {str(e)}")
    except OverflowError:
        logging.warning(f"Overflow in calculation for: {expression[:50]}")
        raise CalculatorError("Result exceeds allowed range")
    except Exception as e:
        logging.error(f"Unexpected error in calculate_with_timeout: {str(e)}", exc_info=True)
        raise CalculatorError(f"Calculation failed: {str(e)}")
    
# ----------------------------------------------------------------
# EQUATION SOLVERS WITH ERROR HANDLING
# ----------------------------------------------------------------

# pq-formula solver (uses formatted output)
def solve_pq(p: float, q: float) -> str:
    try:
        discriminant = (p / 2) ** 2 - q

        if discriminant < 0:
            return "No real roots (discriminant < 0)"
        elif abs(discriminant) < 1e-10:
            x = -p / 2
            return f"x = {format_number(x)} (repeated root)"
        else:
            x1 = -p / 2 + math.sqrt(discriminant)
            x2 = -p / 2 - math.sqrt(discriminant)
            return f"x₁ = {format_number(x1)}\nx₂ = {format_number(x2)}"
    except (ValueError, OverflowError) as e:
        logging.error(f"Error in solve_pq: {str(e)}")
        raise CalculatorError(f"Cannot solve PQ equation: {str(e)}")

# Quadratic formula solver (uses formatted output)
def solve_quadratic(a: float, b: float, c: float) -> str:
    try:
        if abs(a) < 1e-10:
            raise CalculatorError("Coefficient 'a' cannot be zero")
        
        discriminant = b ** 2 - 4 * a * c
        if discriminant < 0:
            return "No real solutions (discriminant < 0)"
        
        sqrt_disc = math.sqrt(discriminant)
        x1 = (-b + sqrt_disc) / (2 * a)
        x2 = (-b - sqrt_disc) / (2 * a)
        return f"x₁ = {format_number(x1)}\nx₂ = {format_number(x2)}"
    except (ValueError, ZeroDivisionError) as e:
        logging.error(f"Error in solve_quadratic: {str(e)}")
        raise CalculatorError(f"Cannot solve quadratic: {str(e)}")

# Equation solver with error handling and formatting
def solve_equation(equation_str: str) -> str:
    try:
        # Input validation
        if not equation_str or len(equation_str) > MAX_EXPRESSION_LENGTH:
            raise CalculatorError("Invalid equation format")
        
        # Define x
        x = symbols('x')
        
        # Remove quotes if present
        equation_str = equation_str.strip('"\'')
        
        # Replace ^ and ² with **
        equation_str = equation_str.replace('^', '**').replace('²', '**2')
        
        # Replace 2x with 2*x for proper multiplication
        equation_str = re.sub(r'(\d)([xy])', r'\1*\2', equation_str)
        
        # Parse and solve the equation
        try:
            expr = sympify(equation_str)
        except sympy.SympifyError as e:
            logging.error(f"Invalid equation syntax: {str(e)}")
            raise CalculatorError(f"Invalid equation format: {str(e)}")
        
        # Solve with timeout
        solutions = solve(expr, x)

        if not solutions:
            return "No valid solutions found!"
        
        # Format solutions
        formatted_solutions = []
        for i, sol in enumerate(solutions, start=1):
            try:
                sol = complex(sol.evalf())
                if abs(sol.imag) < 1e-10:
                    formatted_solutions.append(f"x{i} = {format_number(sol.real)}")
                else:
                    formatted_solutions.append(f"x{i} = {format_number(sol.real)} + {format_number(sol.imag)}i")
            except (ValueError, TypeError) as e:
                logging.warning(f"Error formatting solution {i}: {str(e)}")
                formatted_solutions.append(f"x{i} = {str(sol)}")

        return "\n".join(formatted_solutions)
    
    # Error handling
    except CalculatorError:
        raise
    except sympy.SympifyError as e:
        logging.error(f"Sympy error in solve_equation: {str(e)}")
        raise CalculatorError(f"Invalid equation: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error in solve_equation: {str(e)}", exc_info=True)
        raise CalculatorError(f"Failed to solve equation: {str(e)}")

# System of equations solver with error handling (formatted output)
def solve_equation_system(equations: list) -> str:
    try:
        if not equations or len(equations) == 0:
            raise CalculatorError("No equations provided")
        
        if len(equations) > MAX_VARIABLES_IN_EQUATION:
            raise CalculatorError(f"Too many equations (max {MAX_VARIABLES_IN_EQUATION})")
        
        # Parse the equations
        parsed_equations = []
        for eq in equations:
            if not eq or len(eq) > MAX_EXPRESSION_LENGTH:
                raise CalculatorError("Invalid equation format")
            
            # Replace '^' with '**'
            eq = eq.replace('^', '**')
            
            # Replace 2x with 2*x
            eq = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', eq)
            
            # Convert 'x + y = 5' to 'x + y - 5'
            if '=' in eq:
                lhs, rhs = eq.split('=', 1)
                eq = f"({lhs}) - ({rhs})"
            
            try:
                parsed_equations.append(sympify(eq))
            except sympy.SympifyError as e:
                logging.error(f"Invalid equation: {eq}")
                raise CalculatorError(f"Invalid equation: {str(e)}")

        # Define variables
        all_vars = set(re.findall(r'[a-zA-Z]', ' '.join(equations)))
        if len(all_vars) == 0:
            raise CalculatorError("No variables found in equations")
        
        variables = symbols(' '.join(sorted(all_vars)))

        # Solve the system
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
    
    # Error handling
    except CalculatorError:
        raise
    except ValueError as e:
        logging.error(f"Value error in solve_equation_system: {str(e)}")
        raise CalculatorError(f"Cannot solve system: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error in solve_equation_system: {str(e)}", exc_info=True)
        raise CalculatorError(f"Failed to solve system: {str(e)}")

# ----------------------------------------------------------------
# SAFE FUNCTIONS FOR CALCULATOR
# ----------------------------------------------------------------

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
# MAIN COMMAND HANDLER
# ----------------------------------------------------------------

# Handles the !calc command and sends results with error handling
async def handle_calc_command(client, message, user_message: str) -> Optional[str]:
    if not user_message.startswith('!calc'):
        return
    
    allowed, error_msg = await rate_limiter.check_command_cooldown('calc')
    if not allowed:
        try:
            await message.channel.send(error_msg)
        except discord.Forbidden:
            logging.error(f"No permission to send message in {message.channel}")
        return None
    
    rate_limiter.command_cooldown.set_cooldown('calc')
    
    logging.debug(f"Calculator command received: {user_message}")
    try:
        expression = user_message[6:].strip()  # Remove '!calc ' prefix
        
        if not expression:
            logging.debug("Empty expression, sending help message")
            try:
                await send_help_message(message)
            except discord.Forbidden:
                logging.error(f"No permission to send help message in channel {message.channel.id}")
                return "❌ I don't have permission to send messages here."
            except discord.HTTPException as e:
                logging.error(f"Failed to send help message: {e}")
                return "❌ Failed to send help message."
            return None

        result = await process_calculation(message, expression)
        if result is not None:
            try:
                await send_calculation_result(message, expression, result)
            except discord.Forbidden:
                logging.error(f"No permission to send embed in channel {message.channel.id}")
                return "❌ I don't have permission to send messages here."
            except discord.HTTPException as e:
                logging.error(f"Failed to send result embed: {e}")
                return "❌ Failed to send result."
        else:
            return "❌ Calculation could not be completed."
            
    except CalculatorError as e:
        logging.warning(f"Calculator validation error: {str(e)}")
        return f"❌ {str(e)}"
    except Exception as e:
        logging.error(f"Unexpected error in handle_calc_command: {str(e)}", exc_info=True)
        return "❌ An unexpected error occurred."

# Processes the calculation with security checks and 'ans' support
async def process_calculation(message, expression: str) -> Optional[str]:
    calc_start = time.time()
    
    try:
        # Check for previous result
        if 'ans' in expression:
            if message.author.id not in LAST_RESULT:
                try:
                    await message.channel.send("❌ No previous calculation found. Cannot use 'ans'.")
                except discord.Forbidden:
                    logging.error(f"No permission to send message in channel {message.channel.id}")
                return None
            expression = expression.replace('ans', str(LAST_RESULT[message.author.id]))
            logging.debug(f"Replaced 'ans' with: {LAST_RESULT[message.author.id]}")

        # Safety checks
        is_safe, error_msg = is_safe_expression(expression)
        if not is_safe:
            try:
                await message.channel.send(f"❌ {error_msg}")
            except discord.Forbidden:
                logging.error(f"No permission to send message in {message.channel}")
            return None

        # Replace special characters
        expression = replace_special_characters(expression)
        logging.debug(f"Expression after character replacement: {expression}")

        # Check if the expression contains a solve function
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
    
    # Error handling
    except CalculatorError as e:
        try:
            await message.channel.send(f"❌ {str(e)}")
        except discord.Forbidden:
            logging.error(f"No permission to send message in {message.channel}")
        except discord.HTTPException as ex:
            logging.error(f"Failed to send error message: {ex}")
            logging.warning(f"Calculator error for user {message.author.id}: {str(e)}")
        return None
    except discord.Forbidden:
        logging.error(f"No permission to send message in {message.channel}")
        return None
    except discord.HTTPException as e:
        logging.error(f"HTTP error when sending message: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in process_calculation: {str(e)}", exc_info=True)
        try:
            await message.channel.send("❌ An unexpected error occurred during calculation.")
        except Exception:
            logging.error("Failed to send error notification")
        return None

# Sends calculation result as an embed with error handling
async def send_calculation_result(message, original_expression: str, result) -> None:
    try:
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
        embed.set_footer(text="💡 Tip: Use 'ans' in your next calculation to use the last result!")

        await message.channel.send(embed=embed)
        logging.debug(f"Calculation result sent for {message.author}: {original_expression} = {result}")
        
    except discord.Forbidden:
        logging.error(f"No permission to send embed in {message.channel}")
        raise
    except discord.HTTPException as e:
        logging.error(f"Failed to send embed: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in send_calculation_result: {str(e)}", exc_info=True)
        raise

# Sends help message with usage instructions and examples
async def send_help_message(message) -> None:
    try:
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
            "\n**Special Features:**\n"
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
        logging.debug(f"Help message sent to {message.author} in {message.channel}")
        
    except discord.Forbidden:
        logging.error(f"No permission to send message in {message.channel}")
        raise
    except discord.HTTPException as e:
        logging.error(f"Failed to send help message: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in send_help_message: {str(e)}", exc_info=True)
        raise

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