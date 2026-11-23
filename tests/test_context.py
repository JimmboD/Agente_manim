import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manim_studio.editor import context as context_module
from manim_studio.editor import workspace
from manim_studio.editor.context import ContextError, build_context


class ContextBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.scenes = self.base / "escenas"
        (self.scenes / "helpers").mkdir(parents=True)
        (self.scenes / "partial_movie_files").mkdir()
        (self.base / "plantillas").mkdir()

        (self.scenes / "main.py").write_text("ACTIVE = True\n", encoding="utf-8")
        (self.scenes / "helpers" / "extra.py").write_text("X = 1\n", encoding="utf-8")
        (self.scenes / "helpers" / "notas.md").write_text("# Notas\n", encoding="utf-8")
        (self.scenes / "helpers" / "bin.dat").write_bytes(b"\x00\x01")
        (self.scenes / "partial_movie_files" / "skip.py").write_text("X = 2\n", encoding="utf-8")
        (self.base / "plantillas" / "otra.py").write_text("Y = 3\n", encoding="utf-8")

        self.original_roots = workspace.ROOTS
        workspace.ROOTS = {
            "escenas": (self.scenes, True),
            "plantillas": (self.base / "plantillas", False),
            "mis-plantillas": (self.base / "mis-plantillas", True),
            "audios": (self.base / "audios", True),
            "media": (self.base / "media", False),
        }

    def tearDown(self):
        workspace.ROOTS = self.original_roots
        self.tmp.cleanup()

    def test_buffer_no_agrega_contexto(self):
        result = build_context("escenas/main.py", "buffer")
        self.assertEqual(result["files"], [])
        self.assertEqual(result["chars"], 0)

    def test_files_excluye_activo_y_binarios(self):
        result = build_context(
            "escenas/main.py",
            "files",
            ["escenas/main.py", "escenas/helpers/extra.py", "escenas/helpers/bin.dat"],
        )
        self.assertEqual([item["path"] for item in result["files"]], ["escenas/helpers/extra.py"])

    def test_folder_expande_y_ignora_generados(self):
        result = build_context("escenas/main.py", "folder", ["escenas/helpers"])
        paths = [item["path"] for item in result["files"]]
        self.assertIn("escenas/helpers/extra.py", paths)
        self.assertIn("escenas/helpers/notas.md", paths)
        self.assertNotIn("escenas/helpers/bin.dat", paths)

    def test_project_incluye_texto_del_proyecto(self):
        result = build_context("escenas/main.py", "project")
        paths = [item["path"] for item in result["files"]]
        self.assertIn("escenas/helpers/extra.py", paths)
        self.assertNotIn("escenas/main.py", paths)
        self.assertNotIn("escenas/partial_movie_files/skip.py", paths)
        self.assertNotIn("plantillas/otra.py", paths)

    def test_recorta_archivos_grandes(self):
        with patch.object(context_module, "MAX_FILE_CHARS", 3):
            result = build_context("escenas/main.py", "files", ["escenas/helpers/extra.py"])
        self.assertEqual(result["files"][0]["code"], "X =")
        self.assertTrue(result["truncated"])

    def test_modo_invalido(self):
        with self.assertRaises(ContextError) as ctx:
            build_context("escenas/main.py", " chronic ")
        self.assertEqual(ctx.exception.status, 400)


if __name__ == "__main__":
    unittest.main()
