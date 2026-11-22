import unittest

from manim_studio.editor.code_assistant import (
    CodeAssistantError,
    MockProvider,
    propose_code_change,
    validate_code,
)


class CodeAssistantTests(unittest.TestCase):
    def setUp(self):
        self.code = '"""Escena"""\nFORMAT = "16:9"\nMAX_ITERACIONES = 5\n'
        self.provider = MockProvider()

    def test_format_proposal_is_not_saved_until_applied(self):
        proposal = propose_code_change(
            "cámbialo a 9:16",
            "escenas/main.py",
            self.code,
            provider=self.provider,
        )
        self.assertIn("9:16", proposal["code"])
        self.assertIn('+FORMAT = "9:16"', proposal["code_diff"])
        self.assertIn('-FORMAT = "16:9"', proposal["code_diff"])
        self.assertIn("formato", proposal["summary"])
        self.assertEqual(proposal["path"], "escenas/main.py")

    def test_iterations_and_pace_proposal(self):
        proposal = propose_code_change(
            "usa 3 iteraciones y hazlo más rápido",
            "escenas/main.py",
            self.code,
            provider=self.provider,
        )
        self.assertIn("MAX_ITERACIONES = 3", proposal["code"])
        self.assertIn("Ritmo: acelerado", proposal["code"])
        self.assertEqual(set(proposal["summary"]), {"iteraciones", "ritmo"})

    def test_unknown_request_returns_guidance(self):
        with self.assertRaises(CodeAssistantError) as ctx:
            propose_code_change("fruta cósmica", "escenas/main.py", self.code, provider=self.provider)
        self.assertEqual(ctx.exception.status, 400)

    def test_invalid_code_is_rejected(self):
        with self.assertRaises(CodeAssistantError) as ctx:
            validate_code("def roto(:")
        self.assertEqual(ctx.exception.status, 422)


if __name__ == "__main__":
    unittest.main()
