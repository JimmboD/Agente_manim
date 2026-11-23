import unittest

from manim_studio.editor.code_assistant import (
    CodeAssistantError,
    MockProvider,
    ensure_editable_path,
    make_diff_details,
    propose_code_change,
    validate_proposal,
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

    def test_diff_incluye_hunks_tipo_github(self):
        proposal = propose_code_change(
            "cámbialo a 9:16",
            "escenas/main.py",
            self.code,
            provider=self.provider,
        )
        self.assertTrue(proposal["hunks"])
        self.assertGreater(proposal["stats"]["added"], 0)
        self.assertGreater(proposal["stats"]["removed"], 0)
        first_line = proposal["hunks"][0]["lines"][0]
        self.assertIn(first_line["type"], {"context", "add", "remove"})
        self.assertIn("old", first_line)
        self.assertIn("new", first_line)

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

    def test_txt_proposal_no_pasa_ast_parse(self):
        original = "$$\\textcolor{yellow}{x} + 1 = 2$$\n$$x = 1$$\n"
        proposal = propose_code_change(
            "ponlo en verde",
            "escenas/pasos_algebraicos.txt",
            original,
            provider=self.provider,
        )
        self.assertIn("\\textcolor{green}", proposal["code"])
        self.assertNotIn("\\textcolor{yellow}", proposal["code"])
        self.assertEqual(proposal["path"], "escenas/pasos_algebraicos.txt")

    def test_solo_se_aceptan_py_y_txt(self):
        with self.assertRaises(CodeAssistantError) as ctx:
            ensure_editable_path("escenas/notas.md")
        self.assertEqual(ctx.exception.status, 422)
        with self.assertRaises(CodeAssistantError):
            propose_code_change("cámbialo", "escenas/notas.md", "hola", provider=self.provider)

    def test_unknown_request_returns_guidance(self):
        with self.assertRaises(CodeAssistantError) as ctx:
            propose_code_change("fruta cósmica", "escenas/main.py", self.code, provider=self.provider)
        self.assertEqual(ctx.exception.status, 400)

    def test_invalid_code_is_rejected(self):
        with self.assertRaises(CodeAssistantError) as ctx:
            validate_proposal("escenas/main.py", "def roto(:")
        self.assertEqual(ctx.exception.status, 422)

    def test_diff_details_sin_cambios(self):
        hunks, stats = make_diff_details("a\nb\n", "a\nb\n", "escenas/main.py")
        self.assertEqual(hunks, [])
        self.assertEqual(stats, {"added": 0, "removed": 0})


if __name__ == "__main__":
    unittest.main()
