import tempfile
import unittest
from pathlib import Path

from app.db import Database
from app.ir import default_ir


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "editor.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_project_and_scene_roundtrip(self):
        project = self.db.create_project("Demo")
        ir = default_ir()
        scene = self.db.create_scene(
            project["id"],
            title=ir["title"],
            method=ir["method"],
            ir=ir,
            code="print('hola')",
        )
        loaded = self.db.get_scene(scene["id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["ir"]["method"], "biseccion")
        self.assertEqual(loaded["code"], "print('hola')")

    def test_update_scene(self):
        project = self.db.create_project("Demo")
        scene = self.db.create_scene(
            project["id"],
            title="Escena",
            method="biseccion",
            ir=default_ir(),
            code="old",
        )
        updated = self.db.update_scene(scene["id"], code="new", title="Nueva")
        self.assertEqual(updated["code"], "new")
        self.assertEqual(updated["title"], "Nueva")

    def test_render_lifecycle(self):
        project = self.db.create_project("Demo")
        scene = self.db.create_scene(
            project["id"],
            title="Escena",
            method="biseccion",
            ir=default_ir(),
            code="code",
        )
        render = self.db.create_render(scene["id"], format_id="16:9", quality="low_quality")
        self.assertEqual(render["status"], "queued")
        self.db.update_render(render["id"], status="success", video_url="/media/x.mp4")
        latest = self.db.latest_render(scene["id"], "16:9")
        self.assertEqual(latest["video_url"], "/media/x.mp4")

    def test_list_scenes(self):
        project = self.db.create_project("Demo")
        self.db.create_scene(
            project["id"],
            title="Escena",
            method="biseccion",
            ir=default_ir(),
            code="code",
        )
        scenes = self.db.list_scenes(project["id"])
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["format"], "16:9")


if __name__ == "__main__":
    unittest.main()
