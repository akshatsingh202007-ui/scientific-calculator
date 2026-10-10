
from flask import Flask, render_template, request, jsonify
import re
import sympy as sp

app = Flask(__name__)

x = sp.Symbol("x")
y = sp.Symbol("y")


def nth_root(value, index):
    """Calculate an indexed root, such as the cube root of 8."""
    index = int(index)

    if index < 1 or index > 100:
        raise ValueError("Root index must be between 1 and 100.")

    return sp.real_root(value, index)


ALLOWED_NAMES = {
    "x": x,
    "y": y,
    "pi": sp.pi,
    "e": sp.E,
    "E": sp.E,
    "I": sp.I,
    "i": sp.I,
    "sqrt": sp.sqrt,
    "root": nth_root,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "arcsin": sp.asin,
    "arccos": sp.acos,
    "arctan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "log": sp.log,
    "ln": sp.log,
    "exp": sp.exp,
    "abs": sp.Abs,
    "factorial": sp.factorial,
}


def convert_roots(expression):
    """Convert calculator root notation into root(radicand, index)."""

    # Indexed roots with parenthesized radicands, e.g. 3√(x + 1)
    expression = re.sub(
        r"(\d+)\s*√\s*\(([^()]*)\)",
        lambda m: f"root(({m.group(2)}), {m.group(1)})",
        expression,
    )

    # Indexed roots with numeric radicands, e.g. 3√8
    expression = re.sub(
        r"(\d+)\s*√\s*(\d+(?:\.\d+)?)",
        lambda m: f"root({m.group(2)}, {m.group(1)})",
        expression,
    )

    # Default square root with parentheses, e.g. √(x + 1)
    expression = re.sub(
        r"√\s*\(([^()]*)\)",
        r"sqrt(\1)",
        expression,
    )

    # Default square root with a number, e.g. √4
    expression = re.sub(
        r"√\s*(\d+(?:\.\d+)?)",
        r"sqrt(\1)",
        expression,
    )

    return expression


def parse_expression(expression):
    """Parse a calculator expression using SymPy."""

    if not isinstance(expression, str):
        raise ValueError("Expression must be text.")

    expression = expression.strip()

    if not expression:
        raise ValueError("Please enter an expression.")

    if len(expression) > 300:
        raise ValueError("Expression must be under 300 characters.")

    expression = convert_roots(expression)
    expression = expression.replace("^", "**")
    expression = expression.replace("×", "*")
    expression = expression.replace("÷", "/")
    expression = expression.replace("π", "pi")

    return sp.sympify(
        expression,
        locals=ALLOWED_NAMES,
        evaluate=True,
    )


def format_result(result):
    """Return the exact result and a decimal approximation."""

    result = sp.simplify(result)

    return {
        "exact": str(result),
        "decimal": str(sp.N(result, 12)),
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json(silent=True) or {}

        expression_text = data.get("expression", "")
        operation = data.get("operation", "evaluate")

        expression = parse_expression(expression_text)

        if operation == "evaluate":
            if expression.free_symbols:
                raise ValueError(
                    "Use a numerical expression for evaluation. "
                    "Use x or y for differentiation or integration."
                )

            result = expression

        elif operation == "differentiate":
            variable = data.get("variable", "x")

            if variable not in ("x", "y"):
                raise ValueError("Variable must be x or y.")

            result = sp.diff(expression, ALLOWED_NAMES[variable])

        elif operation == "integrate":
            variable = data.get("variable", "x")

            if variable not in ("x", "y"):
                raise ValueError("Variable must be x or y.")

            result = sp.integrate(expression, ALLOWED_NAMES[variable])

        elif operation == "definite_integrate":
            variable = data.get("variable", "x")

            if variable not in ("x", "y"):
                raise ValueError("Variable must be x or y.")

            lower = parse_expression(str(data.get("lower", "0")))
            upper = parse_expression(str(data.get("upper", "1")))

            if lower.free_symbols or upper.free_symbols:
                raise ValueError("Integration limits must be numeric.")

            if lower.is_real is False or upper.is_real is False:
                raise ValueError("Integration limits must be real numbers.")

            result = sp.integrate(
                expression,
                (ALLOWED_NAMES[variable], lower, upper),
            )

        else:
            raise ValueError("Unknown calculation operation.")

        return jsonify({
            "success": True,
            "result": format_result(result),
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400


if __name__ == "__main__":
    app.run(debug=True)
