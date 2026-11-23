import tempfile
import unittest
from pathlib import Path

from manim_studio.editor import template_bundles, workspace
from manim_studio.editor.template_bundles import TemplateConflictError


class TemplateBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / "escenas").mkdir()
        self.original_roots = workspace.ROOTS
        workspace.ROOTS = {
            "escenas": (self.base / "escenas", True),
            "plantillas": (self.base / "plantillas", False),
            "mis-plantillas": (self.base / "mis-plantillas", True),
            "audios": (self.base / "audios", True),
            "media": (self.base / "media", False),
        }

    def tearDown(self):
        workspace.ROOTS = self.original_roots
        self.tmp.cleanup()

    def test_deploy_crea_script_y_txt_y_abre_python(self):
        result = template_bundles.deploy("pasos_algebraicos")

        self.assertEqual(result["open"], "escenas/pasos_algebraicos.py")
        self.assertEqual(
            {item["path"] for item in result["files"]},
            {"escenas/pasos_algebraicos.py", "escenas/pasos_algebraicos.txt"},
        )
        script = (self.base / "escenas" / "pasos_algebraicos.py").read_text(encoding="utf-8")
        self.assertIn("with_name(\"pasos_algebraicos.txt\")", script)
        self.assertTrue((self.base / "escenas" / "pasos_algebraicos.txt").is_file())

    def test_conflicto_devuelve_sha_y_requiere_confirmacion(self):
        template_bundles.deploy("pasos_algebraicos")

        with self.assertRaises(TemplateConflictError) as ctx:
            template_bundles.deploy("pasos_algebraicos")

        self.assertEqual(ctx.exception.status, 409)
        self.assertEqual(len(ctx.exception.conflicts), 2)
        self.assertTrue(ctx.exception.expected_shas)

        with self.assertRaises(TemplateConflictError):
            template_bundles.deploy(
                "pasos_algebraicos",
                overwrite=True,
                expected_shas={"escenas/pasos_algebraicos.py": "0000"},
            )

        result = template_bundles.deploy(
            "pasos_algebraicos",
            overwrite=True,
            expected_shas=ctx.exception.expected_shas,
        )
        self.assertTrue(all(item["action"] == "overwritten" for item in result["files"]))

    def test_bundle_desconocido(self):
        with self.assertRaises(workspace.WorkspaceError):
            template_bundles.deploy("no_existe")


if __name__ == "__main__":
    unittest.main()
