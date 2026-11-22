import unittest
from unittest.mock import Mock

from app.api import EditorAPI
from app.ir import default_ir


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


if __name__ == "__main__":
    unittest.main()
