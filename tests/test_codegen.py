import ast
import unittest

from manim_studio.editor.codegen import code_diff, generate_code, validate_generated_code
from manim_studio.editor.ir import default_ir


class CodegenTests(unittest.TestCase):
    def test_generated_code_parses(self):
        code = generate_code(default_ir())
        ast.parse(code)
        self.assertIn("construir_biseccion", code)
        self.assertIn("IR = ", code)

    def test_generated_code_is_valid(self):
        validate_generated_code(generate_code(default_ir()))

    def test_rejects_forbidden_import(self):
        with self.assertRaises(ValueError):
            validate_generated_code("import os\n")

    def test_rejects_forbidden_call(self):
        with self.assertRaises(ValueError):
            validate_generated_code("eval('1 + 1')\n")

    def test_diff(self):
        diff = code_diff("a\n", "b\n")
        self.assertIn("-a", diff)
        self.assertIn("+b", diff)


if __name__ == "__main__":
    unittest.main()
