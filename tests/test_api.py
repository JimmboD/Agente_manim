import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from manim_studio.editor.api import ApiError, EditorAPI
from manim_studio.editor.codegen import generate_code
from manim_studio.editor.db import Database
from manim_studio.editor.ir import default_ir
from manim_studio.editor.llm import LLMProposal


class SubmitRenderTests(unittest.TestCase):
    def test_nuevo_render_cancela_el_anterior_de_la_misma_escena(self):
        db = Mock()
        jobs = Mock()
        jobs.submit.return_value = {"id": "nuevo", "status": "queued"}
        llm = Mock()
        api = EditorAPI(db=db, jobs=jobs, llm=llm, token="token")

        ir = default_ir("biseccion")
        scene = {"id": "escena-1", "code": "codigo", "ir": ir}

        result = api._submit_render(scene, {"format": "16:9", "quality": "low_quality"})

        jobs.cancel_scene.assert_called_once_with(
            "escena-1", reason="reemplazado por un render más reciente"
        )
        jobs.submit.assert_called_once()
        self.assertEqual(result["id"], "nuevo")


class FakeLLM:
    name = "fake"

    def __init__(self, patch, *, repair_patch=None):
        self.patch = patch
        self.repair_patch = repair_patch

    def propose(self, message, ir, context=None):
        return LLMProposal("Propuesta lista.", self.patch, ["formato"])

    def repair(self, proposal, error, message, ir, context=None):
        if self.repair_patch is None:
            raise RuntimeError("sin reparación")
        return LLMProposal("Corregido.", self.repair_patch, ["formato"])


class ChatApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "editor.db")
        project = self.db.create_project("Proyecto de prueba")
        ir = default_ir()
        self.scene = self.db.create_scene(
            project["id"],
            title=ir["title"],
            method=ir["method"],
            ir=ir,
            code=generate_code(ir),
        )
        self.jobs = Mock()
        self.jobs.submit.return_value = {"id": "job-1", "status": "queued"}
        self.jobs.active_for_scene.return_value = None

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _api(self, llm):
        return EditorAPI(db=self.db, jobs=self.jobs, llm=llm, token="token")

    def test_chat_no_guarda_el_parche_en_la_escena(self):
        api = self._api(FakeLLM({"format": "9:16"}))

        result = api._chat(self.scene, {"message": "cámbialo a 9:16"})

        self.assertEqual(result["patch"], {"format": "9:16"})
        self.assertEqual(result["scene"]["ir"]["format"], "16:9")
        current = self.db.get_scene(self.scene["id"])
        self.assertEqual(current["ir"]["format"], "16:9")
        self.assertEqual(current["revision"], self.scene["revision"])
        self.jobs.submit.assert_not_called()
        self.assertEqual(len(self.db.list_chat_messages(self.scene["id"])), 2)

    def test_chat_con_parche_invalido_no_modifica_la_escena(self):
        api = self._api(FakeLLM({"formato": "9:16"}))

        result = api._chat(self.scene, {"message": "cámbialo a 9:16"})

        self.assertTrue(result["error"])
        self.assertEqual(result["patch"], {})
        self.assertEqual(self.db.get_scene(self.scene["id"])["ir"]["format"], "16:9")

    def test_chat_repara_un_parche_invalido(self):
        api = self._api(FakeLLM({"formato": "9:16"}, repair_patch={"format": "9:16"}))

        result = api._chat(self.scene, {"message": "cámbialo a 9:16"})

        self.assertEqual(result["patch"], {"format": "9:16"})
        self.assertEqual(self.db.get_scene(self.scene["id"])["ir"]["format"], "16:9")

    def test_apply_guarda_y_lanza_render(self):
        api = self._api(FakeLLM({}))
        base = self.db.get_scene(self.scene["id"])

        result = api._apply(base, {
            "patch": {"format": "9:16"},
            "base_revision": base["revision"],
            "quality": "low_quality",
        })

        current = self.db.get_scene(self.scene["id"])
        self.assertEqual(current["ir"]["format"], "9:16")
        self.assertNotEqual(current["revision"], base["revision"])
        self.jobs.submit.assert_called_once()
        self.assertTrue(result["code_diff"])

    def test_apply_con_revision_obsoleta_devuelve_409(self):
        api = self._api(FakeLLM({}))

        with self.assertRaises(ApiError) as ctx:
            api._apply(self.scene, {"patch": {"format": "9:16"}, "base_revision": 0})

        self.assertEqual(ctx.exception.status, 409)
        self.assertEqual(self.db.get_scene(self.scene["id"])["ir"]["format"], "16:9")

    def test_apply_con_parche_invalido_devuelve_422(self):
        api = self._api(FakeLLM({}))

        with self.assertRaises(ApiError) as ctx:
            api._apply(self.scene, {
                "patch": {"formato": "9:16"},
                "base_revision": self.scene["revision"],
            })

        self.assertEqual(ctx.exception.status, 422)
        self.jobs.submit.assert_not_called()

    def test_apply_acepta_ir_completo_para_deshacer(self):
        api = self._api(FakeLLM({}))
        previous_ir = self.scene["ir"]
        changed = api._apply(self.scene, {
            "patch": {"format": "9:16"},
            "base_revision": self.scene["revision"],
        })
        current = self.db.get_scene(self.scene["id"])

        api._apply(current, {
            "ir": previous_ir,
            "base_revision": current["revision"],
        })

        self.assertEqual(self.db.get_scene(self.scene["id"])["ir"]["format"], "16:9")
        self.assertNotEqual(changed["scene"]["revision"], self.scene["revision"])


if __name__ == "__main__":
    unittest.main()
