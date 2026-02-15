"""Tests for the transforms module."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal

from plottini.core.transforms import (
    Transform,
    apply_transform,
    evaluate_expression,
    validate_expression,
)
from plottini.utils.errors import ExpressionError, ValidationError


class TestTransformEnum:
    """Tests for Transform enum."""

    def test_transform_enum_values(self):
        """Test Transform enum has correct values."""
        assert Transform.LOG.value == "log"
        assert Transform.LOG10.value == "log10"
        assert Transform.LOG2.value == "log2"
        assert Transform.SQUARE.value == "square"
        assert Transform.CUBE.value == "cube"
        assert Transform.SQRT.value == "sqrt"
        assert Transform.CBRT.value == "cbrt"
        assert Transform.SIN.value == "sin"
        assert Transform.COS.value == "cos"
        assert Transform.TAN.value == "tan"
        assert Transform.ARCSIN.value == "arcsin"
        assert Transform.ARCCOS.value == "arccos"
        assert Transform.ARCTAN.value == "arctan"
        assert Transform.ABS.value == "abs"
        assert Transform.INVERSE.value == "inverse"
        assert Transform.EXP.value == "exp"
        assert Transform.NEGATE.value == "negate"

    def test_transform_enum_count(self):
        """Test Transform enum has 17 presets."""
        assert len(Transform) == 17


class TestApplyTransformLogarithmic:
    """Tests for logarithmic transforms."""

    def test_log_valid_data(self):
        """Test LOG transform with valid positive data."""
        data = np.array([1.0, np.e, np.e**2])
        result = apply_transform(data, Transform.LOG)
        expected = np.array([0.0, 1.0, 2.0])
        assert_array_almost_equal(result, expected)

    def test_log_negative_raises_error(self):
        """Test LOG transform raises error on negative values."""
        data = np.array([1.0, -1.0, 2.0])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.LOG)

    def test_log_zero_raises_error(self):
        """Test LOG transform raises error on zero."""
        data = np.array([1.0, 0.0, 2.0])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.LOG)

    def test_log10_valid_data(self):
        """Test LOG10 transform with valid positive data."""
        data = np.array([1.0, 10.0, 100.0])
        result = apply_transform(data, Transform.LOG10)
        expected = np.array([0.0, 1.0, 2.0])
        assert_array_almost_equal(result, expected)

    def test_log10_negative_raises_error(self):
        """Test LOG10 transform raises error on negative values."""
        data = np.array([1.0, -1.0, 2.0])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.LOG10)

    def test_log2_valid_data(self):
        """Test LOG2 transform with valid positive data."""
        data = np.array([1.0, 2.0, 4.0, 8.0])
        result = apply_transform(data, Transform.LOG2)
        expected = np.array([0.0, 1.0, 2.0, 3.0])
        assert_array_almost_equal(result, expected)

    def test_log2_negative_raises_error(self):
        """Test LOG2 transform raises error on negative values."""
        data = np.array([1.0, -1.0, 2.0])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.LOG2)


class TestApplyTransformPower:
    """Tests for power transforms."""

    def test_square(self):
        """Test SQUARE transform."""
        data = np.array([1.0, 2.0, 3.0, -2.0])
        result = apply_transform(data, Transform.SQUARE)
        expected = np.array([1.0, 4.0, 9.0, 4.0])
        assert_array_almost_equal(result, expected)

    def test_cube(self):
        """Test CUBE transform."""
        data = np.array([1.0, 2.0, 3.0, -2.0])
        result = apply_transform(data, Transform.CUBE)
        expected = np.array([1.0, 8.0, 27.0, -8.0])
        assert_array_almost_equal(result, expected)

    def test_sqrt_valid_data(self):
        """Test SQRT transform with valid non-negative data."""
        data = np.array([0.0, 1.0, 4.0, 9.0])
        result = apply_transform(data, Transform.SQRT)
        expected = np.array([0.0, 1.0, 2.0, 3.0])
        assert_array_almost_equal(result, expected)

    def test_sqrt_negative_raises_error(self):
        """Test SQRT transform raises error on negative values."""
        data = np.array([1.0, -1.0, 4.0])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.SQRT)

    def test_cbrt(self):
        """Test CBRT transform (cube root, works on negative)."""
        data = np.array([1.0, 8.0, 27.0, -8.0])
        result = apply_transform(data, Transform.CBRT)
        expected = np.array([1.0, 2.0, 3.0, -2.0])
        assert_array_almost_equal(result, expected)


class TestApplyTransformTrigonometric:
    """Tests for trigonometric transforms."""

    def test_sin(self):
        """Test SIN transform."""
        data = np.array([0.0, np.pi / 2, np.pi])
        result = apply_transform(data, Transform.SIN)
        expected = np.array([0.0, 1.0, 0.0])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_cos(self):
        """Test COS transform."""
        data = np.array([0.0, np.pi / 2, np.pi])
        result = apply_transform(data, Transform.COS)
        expected = np.array([1.0, 0.0, -1.0])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_tan(self):
        """Test TAN transform."""
        data = np.array([0.0, np.pi / 4])
        result = apply_transform(data, Transform.TAN)
        expected = np.array([0.0, 1.0])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_arcsin_valid_data(self):
        """Test ARCSIN transform with valid data in [-1, 1]."""
        data = np.array([0.0, 0.5, 1.0, -1.0])
        result = apply_transform(data, Transform.ARCSIN)
        expected = np.array([0.0, np.pi / 6, np.pi / 2, -np.pi / 2])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_arcsin_out_of_range_raises_error(self):
        """Test ARCSIN raises error if |x| > 1."""
        data = np.array([0.0, 1.5, 0.5])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.ARCSIN)

    def test_arccos_valid_data(self):
        """Test ARCCOS transform with valid data in [-1, 1]."""
        data = np.array([1.0, 0.5, 0.0, -1.0])
        result = apply_transform(data, Transform.ARCCOS)
        expected = np.array([0.0, np.pi / 3, np.pi / 2, np.pi])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_arccos_out_of_range_raises_error(self):
        """Test ARCCOS raises error if |x| > 1."""
        data = np.array([0.0, -1.5, 0.5])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.ARCCOS)

    def test_arctan(self):
        """Test ARCTAN transform (no domain restriction)."""
        data = np.array([0.0, 1.0, -1.0, 100.0])
        result = apply_transform(data, Transform.ARCTAN)
        expected = np.array([0.0, np.pi / 4, -np.pi / 4, np.arctan(100.0)])
        assert_array_almost_equal(result, expected, decimal=10)


class TestApplyTransformOther:
    """Tests for other transforms."""

    def test_abs(self):
        """Test ABS transform."""
        data = np.array([1.0, -2.0, 3.0, -4.0])
        result = apply_transform(data, Transform.ABS)
        expected = np.array([1.0, 2.0, 3.0, 4.0])
        assert_array_almost_equal(result, expected)

    def test_inverse_valid_data(self):
        """Test INVERSE (1/x) transform with non-zero data."""
        data = np.array([1.0, 2.0, 4.0, -2.0])
        result = apply_transform(data, Transform.INVERSE)
        expected = np.array([1.0, 0.5, 0.25, -0.5])
        assert_array_almost_equal(result, expected)

    def test_inverse_zero_raises_error(self):
        """Test INVERSE raises error on zero."""
        data = np.array([1.0, 0.0, 2.0])
        with pytest.raises(ValidationError):
            apply_transform(data, Transform.INVERSE)

    def test_exp(self):
        """Test EXP transform."""
        data = np.array([0.0, 1.0, 2.0])
        result = apply_transform(data, Transform.EXP)
        expected = np.array([1.0, np.e, np.e**2])
        assert_array_almost_equal(result, expected)

    def test_negate(self):
        """Test NEGATE transform."""
        data = np.array([1.0, -2.0, 3.0])
        result = apply_transform(data, Transform.NEGATE)
        expected = np.array([-1.0, 2.0, -3.0])
        assert_array_almost_equal(result, expected)


class TestApplyTransformGeneral:
    """General tests for apply_transform."""

    def test_preserves_array_shape(self):
        """Test transform preserves array shape."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = apply_transform(data, Transform.SQUARE)
        assert result.shape == data.shape

    def test_returns_float64_array(self):
        """Test transform returns float64 array."""
        data = np.array([1.0, 2.0, 3.0])
        result = apply_transform(data, Transform.SQUARE)
        assert result.dtype == np.float64


# ============================================================================
# Expression Evaluator Tests
# ============================================================================


class TestValidateExpression:
    """Tests for validate_expression function."""

    def test_valid_simple_expression(self):
        """Test validation accepts simple valid expressions."""
        assert validate_expression("col1 + col2") is True
        assert validate_expression("col1 - col2") is True
        assert validate_expression("col1 * col2") is True
        assert validate_expression("col1 / col2") is True

    def test_valid_expression_with_constants(self):
        """Test validation accepts expressions with constants."""
        assert validate_expression("col1 * 2 + 1") is True
        assert validate_expression("col1 ** 2") is True

    def test_valid_expression_with_functions(self):
        """Test validation accepts whitelisted functions."""
        assert validate_expression("sqrt(col1)") is True
        assert validate_expression("log(col1)") is True
        assert validate_expression("sin(col1)") is True

    def test_rejects_import(self):
        """Test validation rejects __import__."""
        assert validate_expression("__import__('os')") is False

    def test_rejects_attribute_access(self):
        """Test validation rejects attribute access."""
        assert validate_expression("os.system('ls')") is False

    def test_rejects_lambda(self):
        """Test validation rejects lambda expressions."""
        assert validate_expression("lambda x: x") is False

    def test_rejects_class_access(self):
        """Test validation rejects class/bases access."""
        assert validate_expression("().__class__.__bases__") is False

    def test_rejects_unknown_function(self):
        """Test validation rejects unknown functions."""
        assert validate_expression("unknown_func(col1)") is False
        assert validate_expression("eval('1+1')") is False


class TestEvaluateExpressionArithmetic:
    """Tests for arithmetic operations in evaluate_expression."""

    def test_addition(self):
        """Test addition: col1 + col2."""
        columns = {
            "col1": np.array([1.0, 2.0, 3.0]),
            "col2": np.array([10.0, 20.0, 30.0]),
        }
        result = evaluate_expression("col1 + col2", columns)
        expected = np.array([11.0, 22.0, 33.0])
        assert_array_almost_equal(result, expected)

    def test_subtraction(self):
        """Test subtraction: col1 - col2."""
        columns = {
            "col1": np.array([10.0, 20.0, 30.0]),
            "col2": np.array([1.0, 2.0, 3.0]),
        }
        result = evaluate_expression("col1 - col2", columns)
        expected = np.array([9.0, 18.0, 27.0])
        assert_array_almost_equal(result, expected)

    def test_multiplication(self):
        """Test multiplication: col1 * col2."""
        columns = {
            "col1": np.array([1.0, 2.0, 3.0]),
            "col2": np.array([10.0, 20.0, 30.0]),
        }
        result = evaluate_expression("col1 * col2", columns)
        expected = np.array([10.0, 40.0, 90.0])
        assert_array_almost_equal(result, expected)

    def test_division(self):
        """Test division: col1 / col2."""
        columns = {
            "col1": np.array([10.0, 20.0, 30.0]),
            "col2": np.array([2.0, 4.0, 5.0]),
        }
        result = evaluate_expression("col1 / col2", columns)
        expected = np.array([5.0, 5.0, 6.0])
        assert_array_almost_equal(result, expected)

    def test_power(self):
        """Test power: col1 ** 2."""
        columns = {"col1": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("col1 ** 2", columns)
        expected = np.array([1.0, 4.0, 9.0])
        assert_array_almost_equal(result, expected)

    def test_modulo(self):
        """Test modulo: col1 % 2."""
        columns = {"col1": np.array([1.0, 2.0, 3.0, 4.0, 5.0])}
        result = evaluate_expression("col1 % 2", columns)
        expected = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
        assert_array_almost_equal(result, expected)

    def test_unary_minus(self):
        """Test unary minus: -col1."""
        columns = {"col1": np.array([1.0, -2.0, 3.0])}
        result = evaluate_expression("-col1", columns)
        expected = np.array([-1.0, 2.0, -3.0])
        assert_array_almost_equal(result, expected)

    def test_with_constants(self):
        """Test expression with constants: col1 * 2 + 1."""
        columns = {"col1": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("col1 * 2 + 1", columns)
        expected = np.array([3.0, 5.0, 7.0])
        assert_array_almost_equal(result, expected)


class TestEvaluateExpressionFunctions:
    """Tests for function calls in evaluate_expression."""

    def test_sqrt(self):
        """Test sqrt function."""
        columns = {"col1": np.array([1.0, 4.0, 9.0])}
        result = evaluate_expression("sqrt(col1)", columns)
        expected = np.array([1.0, 2.0, 3.0])
        assert_array_almost_equal(result, expected)

    def test_log(self):
        """Test log function."""
        columns = {"col1": np.array([1.0, np.e, np.e**2])}
        result = evaluate_expression("log(col1)", columns)
        expected = np.array([0.0, 1.0, 2.0])
        assert_array_almost_equal(result, expected)

    def test_log10(self):
        """Test log10 function."""
        columns = {"col1": np.array([1.0, 10.0, 100.0])}
        result = evaluate_expression("log10(col1)", columns)
        expected = np.array([0.0, 1.0, 2.0])
        assert_array_almost_equal(result, expected)

    def test_log2(self):
        """Test log2 function."""
        columns = {"col1": np.array([1.0, 2.0, 4.0])}
        result = evaluate_expression("log2(col1)", columns)
        expected = np.array([0.0, 1.0, 2.0])
        assert_array_almost_equal(result, expected)

    def test_sin(self):
        """Test sin function."""
        columns = {"col1": np.array([0.0, np.pi / 2, np.pi])}
        result = evaluate_expression("sin(col1)", columns)
        expected = np.array([0.0, 1.0, 0.0])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_cos(self):
        """Test cos function."""
        columns = {"col1": np.array([0.0, np.pi / 2, np.pi])}
        result = evaluate_expression("cos(col1)", columns)
        expected = np.array([1.0, 0.0, -1.0])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_tan(self):
        """Test tan function."""
        columns = {"col1": np.array([0.0, np.pi / 4])}
        result = evaluate_expression("tan(col1)", columns)
        expected = np.array([0.0, 1.0])
        assert_array_almost_equal(result, expected, decimal=10)

    def test_abs(self):
        """Test abs function."""
        columns = {"col1": np.array([1.0, -2.0, 3.0, -4.0])}
        result = evaluate_expression("abs(col1)", columns)
        expected = np.array([1.0, 2.0, 3.0, 4.0])
        assert_array_almost_equal(result, expected)

    def test_exp(self):
        """Test exp function."""
        columns = {"col1": np.array([0.0, 1.0, 2.0])}
        result = evaluate_expression("exp(col1)", columns)
        expected = np.array([1.0, np.e, np.e**2])
        assert_array_almost_equal(result, expected)


class TestEvaluateExpressionComplex:
    """Tests for complex expressions."""

    def test_complex_expression(self):
        """Test complex expression: sqrt(col1**2 + col2**2)."""
        columns = {
            "col1": np.array([3.0, 5.0, 8.0]),
            "col2": np.array([4.0, 12.0, 15.0]),
        }
        result = evaluate_expression("sqrt(col1**2 + col2**2)", columns)
        expected = np.array([5.0, 13.0, 17.0])
        assert_array_almost_equal(result, expected)

    def test_quoted_column_name(self):
        """Test expression with quoted column name."""
        columns = {
            "Column Name": np.array([1.0, 2.0, 3.0]),
        }
        result = evaluate_expression('"Column Name" + 1', columns)
        expected = np.array([2.0, 3.0, 4.0])
        assert_array_almost_equal(result, expected)


class TestEvaluateExpressionErrors:
    """Tests for error handling in evaluate_expression."""

    def test_undefined_column_raises_error(self):
        """Test undefined column raises ExpressionError."""
        columns = {"col1": np.array([1.0, 2.0, 3.0])}
        with pytest.raises(ExpressionError):
            evaluate_expression("col1 + undefined_col", columns)

    def test_division_by_zero_raises_error(self):
        """Test division by zero raises ExpressionError."""
        columns = {
            "col1": np.array([1.0, 2.0, 3.0]),
            "col2": np.array([1.0, 0.0, 1.0]),
        }
        with pytest.raises(ExpressionError):
            evaluate_expression("col1 / col2", columns)

    def test_log_negative_raises_error(self):
        """Test log of negative raises ExpressionError."""
        columns = {"col1": np.array([1.0, -1.0, 2.0])}
        with pytest.raises(ExpressionError):
            evaluate_expression("log(col1)", columns)

    def test_sqrt_negative_raises_error(self):
        """Test sqrt of negative raises ExpressionError."""
        columns = {"col1": np.array([1.0, -1.0, 4.0])}
        with pytest.raises(ExpressionError):
            evaluate_expression("sqrt(col1)", columns)

    def test_invalid_expression_raises_error(self):
        """Test invalid expression raises ExpressionError."""
        columns = {"col1": np.array([1.0, 2.0, 3.0])}
        with pytest.raises(ExpressionError):
            evaluate_expression("__import__('os')", columns)


class TestApplyTransformEdgeCases:
    """Edge case tests for apply_transform."""

    def test_transform_empty_array(self):
        """Test transform with empty array."""
        data = np.array([], dtype=np.float64)
        result = apply_transform(data, Transform.SQUARE)
        assert len(result) == 0
        assert result.dtype == np.float64

    def test_transform_single_element(self):
        """Test transform with single element array."""
        data = np.array([4.0], dtype=np.float64)
        result = apply_transform(data, Transform.SQRT)
        assert_array_almost_equal(result, [2.0])

    def test_transform_large_array(self):
        """Test transform with large array for performance."""
        data = np.arange(1.0, 10001.0, dtype=np.float64)
        result = apply_transform(data, Transform.LOG10)
        assert len(result) == 10000
        assert_array_almost_equal(result[0], 0.0)
        assert_array_almost_equal(result[-1], 4.0)

    def test_all_transforms_on_valid_data(self):
        """Test all transforms work on appropriate valid data."""
        # Data valid for most transforms
        data = np.array([0.5, 1.0, 2.0], dtype=np.float64)

        # Log transforms need positive values
        assert len(apply_transform(data, Transform.LOG)) == 3
        assert len(apply_transform(data, Transform.LOG10)) == 3
        assert len(apply_transform(data, Transform.LOG2)) == 3

        # Power transforms work on any values
        assert len(apply_transform(data, Transform.SQUARE)) == 3
        assert len(apply_transform(data, Transform.CUBE)) == 3
        assert len(apply_transform(data, Transform.SQRT)) == 3
        assert len(apply_transform(data, Transform.CBRT)) == 3

        # Trig transforms work on any values
        assert len(apply_transform(data, Transform.SIN)) == 3
        assert len(apply_transform(data, Transform.COS)) == 3
        assert len(apply_transform(data, Transform.TAN)) == 3
        assert len(apply_transform(data, Transform.ARCTAN)) == 3

        # Arc trig needs [-1, 1]
        arcsin_data = np.array([-0.5, 0.0, 0.5], dtype=np.float64)
        assert len(apply_transform(arcsin_data, Transform.ARCSIN)) == 3
        assert len(apply_transform(arcsin_data, Transform.ARCCOS)) == 3

        # Other transforms
        assert len(apply_transform(data, Transform.ABS)) == 3
        assert len(apply_transform(data, Transform.INVERSE)) == 3
        assert len(apply_transform(data, Transform.EXP)) == 3
        assert len(apply_transform(data, Transform.NEGATE)) == 3


class TestEvaluateExpressionEdgeCases:
    """Edge case tests for evaluate_expression."""

    def test_expression_with_nested_parentheses(self):
        """Test expression evaluation with nested parentheses."""
        columns = {"x": np.array([2.0, 3.0, 4.0])}
        result = evaluate_expression("((x + 1) * 2) - 1", columns)
        expected = np.array([5.0, 7.0, 9.0])
        assert_array_almost_equal(result, expected)

    def test_expression_with_multiple_operators(self):
        """Test expression with multiple chained operators."""
        columns = {"x": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("x + x * x - x / x", columns)
        # x + x^2 - 1 = [1 + 1 - 1, 2 + 4 - 1, 3 + 9 - 1] = [1, 5, 11]
        expected = np.array([1.0, 5.0, 11.0])
        assert_array_almost_equal(result, expected)

    def test_expression_with_float_constants(self):
        """Test expression with float constants."""
        columns = {"x": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("x * 1.5 + 0.5", columns)
        expected = np.array([2.0, 3.5, 5.0])
        assert_array_almost_equal(result, expected)

    def test_expression_with_negative_constants(self):
        """Test expression with negative constants."""
        columns = {"x": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("x * -2", columns)
        expected = np.array([-2.0, -4.0, -6.0])
        assert_array_almost_equal(result, expected)

    def test_expression_column_only(self):
        """Test expression that's just a column reference."""
        columns = {"x": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("x", columns)
        expected = np.array([1.0, 2.0, 3.0])
        assert_array_almost_equal(result, expected)

    def test_expression_constant_only(self):
        """Test expression that's just a constant."""
        columns = {"x": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("42", columns)
        # Result could be scalar or array - just check it evaluates
        if isinstance(result, np.ndarray):
            assert result.size >= 1
        else:
            assert result == 42

    def test_expression_with_all_allowed_functions(self):
        """Test expressions using all allowed functions."""
        columns = {"x": np.array([1.0, 4.0, 9.0])}

        # Test each allowed function
        assert len(evaluate_expression("sqrt(x)", columns)) == 3
        assert len(evaluate_expression("log(x)", columns)) == 3
        assert len(evaluate_expression("log10(x)", columns)) == 3
        assert len(evaluate_expression("log2(x)", columns)) == 3
        assert len(evaluate_expression("abs(x)", columns)) == 3
        assert len(evaluate_expression("sin(x)", columns)) == 3
        assert len(evaluate_expression("cos(x)", columns)) == 3
        assert len(evaluate_expression("tan(x)", columns)) == 3
        assert len(evaluate_expression("exp(x / 10)", columns)) == 3

    def test_expression_underscore_column_name(self):
        """Test expression with underscore in column name."""
        columns = {"my_column": np.array([1.0, 2.0, 3.0])}
        result = evaluate_expression("my_column * 2", columns)
        expected = np.array([2.0, 4.0, 6.0])
        assert_array_almost_equal(result, expected)

    def test_expression_multiple_columns_same_name_prefix(self):
        """Test expression with columns that have similar names."""
        columns = {
            "col": np.array([1.0, 2.0, 3.0]),
            "col1": np.array([10.0, 20.0, 30.0]),
            "col12": np.array([100.0, 200.0, 300.0]),
        }
        result = evaluate_expression("col + col1 + col12", columns)
        expected = np.array([111.0, 222.0, 333.0])
        assert_array_almost_equal(result, expected)
