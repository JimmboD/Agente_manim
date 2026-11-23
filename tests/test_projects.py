import tempfile
import unittest
from pathlib import Path
from unittest import mock

from manim_studio.editor import projects, workspace
from manim_studio.editor.workspace import WorkspaceError
from manim_studio import servidor


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.projects_dir = self.base / "proyectos"
        self.data_dir = self.base / "data"
        self.legacy = self.base / "escenas_legacy"
        self.projects_dir.mkdir()
        self.data_dir.mkdir()
        self.legacy.mkdir()
        self.patches = [
            mock.patch.object(projects, "PROJECTS_DIR", self.projects_dir),
            mock.patch.object(projects, "DATA_DIR", self.data_dir),
            mock.patch.object(projects, "ACTIVE_FILE", self.data_dir / "active_project"),
            mock.patch.object(projects, "SETTINGS_FILE", self.data_dir / "settings.json"),
            mock.patch.object(projects, "ESCENAS_DIR", self.legacy),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        workspace.ROOTS["escenas"] = (workspace.ESCENAS_DIR, True)
        self.tmp.cleanup()

    def test_create_select_and_delete_project(self):
        first = projects.create_project("Mi proyecto")
        second = projects.create_project("Otro proyecto")
        self.assertEqual([p["slug"] for p in projects.list_projects()], [first["slug"], second["slug"]])
        self.assertEqual(projects.active_slug(), second["slug"])
        self.assertTrue((projects.scenes_dir(first["slug"]) / "main.py").is_file())

        projects.set_active(first["slug"])
        self.assertEqual(projects.active_slug(), first["slug"])

        result = projects.delete_project(first["slug"])
        self.assertEqual(result["active"], second["slug"])
        self.assertEqual(len(projects.list_projects()), 1)

    def test_initial_project_migrates_legacy_files_byte_for_byte(self):
        source = self.legacy / "main.py"
        source.write_bytes(b"x = 'contenido del usuario'\n")
        (self.legacy / "pasos_algebraicos.txt").write_text("pasos", encoding="utf-8")

        initial = projects.ensure_initial_project()
        copied = projects.main_py_path(initial["slug"]).read_bytes()
        self.assertEqual(copied, b"x = 'contenido del usuario'\n")
        self.assertTrue(projects.pasos_path(initial["slug"]).is_file())
        self.assertEqual(projects.active_slug(), initial["slug"])

    def test_settings_are_persisted(self):
        self.assertFalse(projects.get_settings()["unlockSystemTemplates"])
        projects.update_settings({"unlockSystemTemplates": True})
        self.assertTrue(projects.get_settings()["unlockSystemTemplates"])

    def test_run_target_uses_open_file_and_never_falls_back_to_main(self):
        slug = "proyecto"
        scenes = self.projects_dir / slug / "escenas"
        scenes.mkdir(parents=True)
        (scenes / "a.py").write_text("print('A')\n", encoding="utf-8")
        main = scenes / "main.py"
        main.write_text("print('MAIN')\n", encoding="utf-8")

        original_roots = dict(workspace.ROOTS)
        original_active = servidor.projects.active_slug
        try:
            workspace.ROOTS["escenas"] = (scenes, True)
            with mock.patch.object(servidor.projects, "active_slug", return_value=slug):
                target = servidor.resolve_run_target(
                    {"path": "escenas/a.py", "project": slug, "format": "9:16"}
                )
                self.assertEqual(Path(target["script"]), (scenes / "a.py").resolve())
                self.assertEqual(target["format"], "9:16")

                with self.assertRaises(WorkspaceError):
                    servidor.resolve_run_target({"path": "plantillas/demo.py", "project": slug})
                with self.assertRaises(WorkspaceError):
                    servidor.resolve_run_target({"path": "escenas/notas.txt", "project": slug})
                with self.assertRaises(WorkspaceError):
                    servidor.resolve_run_target({"path": "escenas/../servidor.py", "project": slug})
        finally:
            workspace.ROOTS.clear()
            workspace.ROOTS.update(original_roots)
            servidor.projects.active_slug = original_active


if __name__ == "__main__":
    unittest.main()
