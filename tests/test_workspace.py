import tempfile
import unittest
from pathlib import Path

from manim_studio.editor import workspace
from manim_studio.editor.workspace import WorkspaceError


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        for name in ("escenas", "plantillas", "mis-plantillas", "audios", "media"):
            (self.base / name).mkdir()
        self.original_roots = workspace.ROOTS
        self.original_templates = workspace.USER_TEMPLATES_DIR
        workspace.ROOTS = {
            "escenas": (self.base / "escenas", True),
            "plantillas": (self.base / "plantillas", False),
            "mis-plantillas": (self.base / "mis-plantillas", True),
            "audios": (self.base / "audios", True),
            "media": (self.base / "media", False),
        }
        workspace.USER_TEMPLATES_DIR = self.base / "mis-plantillas"

    def tearDown(self):
        workspace.ROOTS = self.original_roots
        workspace.USER_TEMPLATES_DIR = self.original_templates
        self.tmp.cleanup()

    def test_tree_and_text_roundtrip(self):
        created = workspace.create("escenas/demo.py", "file")
        self.assertEqual(created["path"], "escenas/demo.py")
        doc = workspace.read("escenas/demo.py")
        self.assertEqual(doc["code"], "")
        saved = workspace.write("escenas/demo.py", 'x = "hola"\n', doc["sha256"])
        self.assertNotEqual(saved["sha256"], doc["sha256"])
        self.assertEqual(workspace.read("escenas/demo.py")["code"], 'x = "hola"\n')
        paths = [node["path"] for root in workspace.tree()["roots"] for node in root["children"]]
        self.assertIn("escenas/demo.py", paths)

    def test_stale_write_returns_conflict(self):
        workspace.create("escenas/main.py", "file")
        first = workspace.write("escenas/main.py", "a = 1\n")
        workspace.write("escenas/main.py", "a = 2\n", first["sha256"])
        with self.assertRaises(WorkspaceError) as ctx:
            workspace.write("escenas/main.py", "a = 3\n", first["sha256"])
        self.assertEqual(ctx.exception.status, 409)

    def test_rejects_traversal_and_readonly_roots(self):
        with self.assertRaises(WorkspaceError):
            workspace.read("escenas/../server.py")
        with self.assertRaises(WorkspaceError) as ctx:
            workspace.write("plantillas/demo.py", "x = 1\n")
        self.assertEqual(ctx.exception.status, 403)

    def test_move_and_delete(self):
        workspace.create("escenas/original.py", "file")
        moved = workspace.move("escenas/original.py", "escenas/renombrado.py")
        self.assertEqual(moved["path"], "escenas/renombrado.py")
        deleted = workspace.delete("escenas/renombrado.py")
        self.assertEqual(deleted["deleted"], "escenas/renombrado.py")
        with self.assertRaises(WorkspaceError):
            workspace.read("escenas/renombrado.py")

    def test_template_creation_validates_python(self):
        with self.assertRaises(WorkspaceError) as ctx:
            workspace.create_template("rota", "def mal(:")
        self.assertEqual(ctx.exception.status, 422)
        template = workspace.create_template("Mi plantilla", "x = 1\n")
        self.assertEqual(template["origin"], "user")
        self.assertIn("mis-plantillas%2fmi_plantilla.py", template["source"].lower())
        self.assertTrue(any(item["id"] == template["id"] for item in workspace.templates()["templates"]))

    def test_rejects_non_audio_upload(self):
        with self.assertRaises(WorkspaceError):
            workspace.upload_audio("virus.py", "ZHVtbXk=")


if __name__ == "__main__":
    unittest.main()
