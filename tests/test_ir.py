import unittest

from manim_studio.editor.ir import (
    IRValidationError,
    default_ir,
    evaluate_expression,
    merge_patch,
    normalize_ir,
    validate_expression,
)


class ExpressionTests(unittest.TestCase):
    def test_accepts_math_expression(self):
        validate_expression("math.exp(x) - 3 * (x ** 2)")
        validate_expression("sin(x) + cos(2 * x)")
        validate_expression("sqrt(abs(x))")

    def test_rejects_import(self):
        with self.assertRaises(IRValidationError):
            validate_expression("__import__('os').system('calc')")

    def test_rejects_attribute_escape(self):
        with self.assertRaises(IRValidationError):
            validate_expression("x.__class__")

    def test_rejects_open(self):
        with self.assertRaises(IRValidationError):
            validate_expression("open('secret.txt')")

    def test_rejects_lambda(self):
        with self.assertRaises(IRValidationError):
            validate_expression("(lambda: 1)()")

    def test_evaluate(self):
        self.assertAlmostEqual(evaluate_expression("x ** 2 - 2", 2), 2.0)


class IRTests(unittest.TestCase):
    def test_default_ir(self):
        ir = default_ir()
        self.assertEqual(ir["method"], "biseccion")
        self.assertEqual(len(ir["beats"]), 9)
        self.assertEqual(ir["params"]["max_iterations"], 5)

    def test_rejects_same_sign_interval(self):
        with self.assertRaises(IRValidationError):
            default_ir(function={"python": "x ** 2 + 1", "latex": "f(x)=x^2+1", "domain": [-5, 5]})

    def test_rejects_interval_outside_domain(self):
        with self.assertRaises(IRValidationError):
            default_ir(params={"a": -10, "b": 1})

    def test_merge_patch_updates_params(self):
        ir = default_ir()
        patched = merge_patch(ir, {"params": {"max_iterations": 3}})
        self.assertEqual(patched["params"]["max_iterations"], 3)
        iterations = [b for b in patched["beats"] if b["kind"] == "iteration"]
        self.assertEqual(len(iterations), 3)

    def test_merge_patch_rejects_unknown_keys(self):
        with self.assertRaises(IRValidationError):
            merge_patch(default_ir(), {"shell": "rm -rf /"})

    def test_format_normalization(self):
        ir = normalize_ir({**default_ir(), "format": "9:16"})
        self.assertEqual(ir["format"], "9:16")


if __name__ == "__main__":
    unittest.main()
