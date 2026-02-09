"""Transforms module for mathematical transformations.

This module provides preset transformations and safe expression evaluation
for derived columns.
"""

from __future__ import annotations

import ast
import operator
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray

from plottini.utils.errors import ExpressionError, ValidationError


class Transform(Enum):
    """Available preset transformations.

    Attributes:
        LOG: Natural logarithm
        LOG10: Base-10 logarithm
        LOG2: Base-2 logarithm
        SQUARE: Square (x^2)
        CUBE: Cube (x^3)
        SQRT: Square root
        CBRT: Cube root
        SIN: Sine
        COS: Cosine
        TAN: Tangent
        ARCSIN: Arcsine (inverse sine)
        ARCCOS: Arccosine (inverse cosine)
        ARCTAN: Arctangent (inverse tangent)
        ABS: Absolute value
        INVERSE: Inverse (1/x)
        EXP: Exponential (e^x)
        NEGATE: Negation (-x)
    """

    LOG = "log"
    LOG10 = "log10"
    LOG2 = "log2"
    SQUARE = "square"
    CUBE = "cube"
    SQRT = "sqrt"
    CBRT = "cbrt"
    SIN = "sin"
    COS = "cos"
    TAN = "tan"
    ARCSIN = "arcsin"
    ARCCOS = "arccos"
    ARCTAN = "arctan"
    ABS = "abs"
    INVERSE = "inverse"
    EXP = "exp"
    NEGATE = "negate"


def apply_transform(
    data: NDArray[np.float64],
    transform: Transform,
) -> NDArray[np.float64]:
    """Apply a preset transformation to data.

    Args:
        data: Input array of numeric values.
        transform: Transform to apply.

    Returns:
        Transformed array.

    Raises:
        ValidationError: If input data is not valid for the transform.
    """
    # Validate input for transforms with domain restrictions
    if transform in (Transform.LOG, Transform.LOG10, Transform.LOG2):
        if np.any(data <= 0):
            raise ValidationError(
                message=f"{transform.value} requires positive values",
                field="data",
                value="contains non-positive values",
            )

    if transform == Transform.SQRT:
        if np.any(data < 0):
            raise ValidationError(
                message="sqrt requires non-negative values",
                field="data",
                value="contains negative values",
            )

    if transform in (Transform.ARCSIN, Transform.ARCCOS):
        if np.any(np.abs(data) > 1):
            raise ValidationError(
                message=f"{transform.value} requires values in [-1, 1]",
                field="data",
                value="contains values outside [-1, 1]",
            )

    if transform == Transform.INVERSE:
        if np.any(data == 0):
            raise ValidationError(
                message="inverse (1/x) requires non-zero values",
                field="data",
                value="contains zero",
            )

    # Apply transform
    if transform == Transform.LOG:
        return np.log(data)
    elif transform == Transform.LOG10:
        return np.log10(data)
    elif transform == Transform.LOG2:
        return np.log2(data)
    elif transform == Transform.SQUARE:
        return data**2
    elif transform == Transform.CUBE:
        return data**3
    elif transform == Transform.SQRT:
        return np.sqrt(data)
    elif transform == Transform.CBRT:
        return np.cbrt(data)
    elif transform == Transform.SIN:
        return np.sin(data)
    elif transform == Transform.COS:
        return np.cos(data)
    elif transform == Transform.TAN:
        return np.tan(data)
    elif transform == Transform.ARCSIN:
        return np.arcsin(data)
    elif transform == Transform.ARCCOS:
        return np.arccos(data)
    elif transform == Transform.ARCTAN:
        return np.arctan(data)
    elif transform == Transform.ABS:
        return np.abs(data)
    elif transform == Transform.INVERSE:
        return 1.0 / data
    elif transform == Transform.EXP:
        return np.exp(data)
    elif transform == Transform.NEGATE:
        return -data
    else:
        # This should never happen with a proper enum
        raise ValueError(f"Unknown transform: {transform}")


# ============================================================================
# Safe Expression Evaluator
# ============================================================================

# Allowed AST node types
ALLOWED_NODES = {
    ast.Expression,  # Top-level
    ast.BinOp,  # a + b, a * b, etc.
    ast.UnaryOp,  # -x, +x
    ast.Constant,  # Numeric literals (Python >= 3.8)
    ast.Name,  # Column references
    ast.Call,  # Function calls (validated separately)
    ast.Load,  # Variable loading context
}

# Allowed binary operators
ALLOWED_BINOPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

# Allowed unary operators
ALLOWED_UNARYOPS: dict[type, Any] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Allowed function names mapped to numpy functions
ALLOWED_FUNCTIONS: dict[str, Any] = {
    "log": np.log,
    "log10": np.log10,
    "log2": np.log2,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
}


def validate_expression(expression: str) -> bool:
    """Check if an expression is safe to evaluate.

    Args:
        expression: Mathematical expression to validate.

    Returns:
        True if expression is safe, False otherwise.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        return _validate_node(tree)
    except SyntaxError:
        return False


def _validate_node(node: ast.AST) -> bool:
    """Recursively validate an AST node.

    Args:
        node: AST node to validate.

    Returns:
        True if node and all children are safe.
    """
    # Check node type is allowed
    if type(node) not in ALLOWED_NODES:
        return False

    # Validate specific node types
    if isinstance(node, ast.BinOp):
        if type(node.op) not in ALLOWED_BINOPS:
            return False
        return _validate_node(node.left) and _validate_node(node.right)

    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in ALLOWED_UNARYOPS:
            return False
        return _validate_node(node.operand)

    elif isinstance(node, ast.Call):
        # Only allow simple function calls with Name as func
        if not isinstance(node.func, ast.Name):
            return False
        if node.func.id not in ALLOWED_FUNCTIONS:
            return False
        # Validate all arguments
        return all(_validate_node(arg) for arg in node.args)

    elif isinstance(node, ast.Expression):
        return _validate_node(node.body)

    elif isinstance(node, ast.Constant):
        # Only allow numeric constants
        return isinstance(node.value, (int, float, str))

    elif isinstance(node, ast.Name):
        # Column references are allowed
        return True

    elif isinstance(node, ast.Load):
        return True

    return False


def evaluate_expression(
    expression: str,
    columns: dict[str, NDArray[np.float64]],
) -> NDArray[np.float64]:
    """Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate.
        columns: Dictionary mapping column names to data arrays.

    Returns:
        Result array.

    Raises:
        ExpressionError: If expression is invalid or evaluation fails.
    """
    # Validate expression first
    if not validate_expression(expression):
        raise ExpressionError(
            message="Invalid or unsafe expression",
            expression=expression,
            detail="Expression contains disallowed operations",
        )

    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate_node(tree.body, columns)

        # Validate result for invalid values
        if np.any(np.isnan(result)):
            raise ExpressionError(
                message="Expression produced invalid result (NaN)",
                expression=expression,
                detail="Check for invalid operations like log of negative",
            )
        if np.any(np.isinf(result)):
            raise ExpressionError(
                message="Expression produced infinite result",
                expression=expression,
                detail="Check for division by zero",
            )

        return result

    except ExpressionError:
        raise
    except Exception as e:
        raise ExpressionError(
            message="Expression evaluation failed",
            expression=expression,
            detail=str(e),
        ) from e


def _evaluate_node(
    node: ast.AST,
    columns: dict[str, NDArray[np.float64]],
) -> NDArray[np.float64]:
    """Recursively evaluate an AST node.

    Args:
        node: AST node to evaluate.
        columns: Dictionary mapping column names to data arrays.

    Returns:
        Result array.

    Raises:
        ExpressionError: If evaluation fails.
    """
    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left, columns)
        right = _evaluate_node(node.right, columns)
        op_func = ALLOWED_BINOPS[type(node.op)]
        result: NDArray[np.float64] = op_func(left, right)
        return result

    elif isinstance(node, ast.UnaryOp):
        operand = _evaluate_node(node.operand, columns)
        op_func = ALLOWED_UNARYOPS[type(node.op)]
        result = op_func(operand)
        return result

    elif isinstance(node, ast.Call):
        func_name = node.func.id  # type: ignore
        func = ALLOWED_FUNCTIONS[func_name]
        args = [_evaluate_node(arg, columns) for arg in node.args]
        result = func(*args)
        return result

    elif isinstance(node, ast.Constant):
        value = node.value
        # Handle quoted column names (strings)
        if isinstance(value, str):
            if value not in columns:
                raise ExpressionError(
                    message=f"Column '{value}' not found",
                    detail=f"Available columns: {', '.join(columns.keys())}",
                )
            return columns[value]
        # Numeric constant - broadcast to array shape
        # Get shape from first column
        first_col = next(iter(columns.values()))
        return np.full(first_col.shape, value, dtype=np.float64)

    elif isinstance(node, ast.Name):
        col_name = node.id
        if col_name not in columns:
            raise ExpressionError(
                message=f"Column '{col_name}' not found",
                detail=f"Available columns: {', '.join(columns.keys())}",
            )
        return columns[col_name]

    else:
        raise ExpressionError(
            message=f"Unsupported node type: {type(node).__name__}",
        )


__all__ = ["Transform", "apply_transform", "validate_expression", "evaluate_expression"]
