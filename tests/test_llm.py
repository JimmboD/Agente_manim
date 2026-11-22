import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from manim_studio.editor import llm
from manim_studio.editor.ir import default_ir, merge_patch
from manim_studio.editor.llm import (
    LLMError,
    MockProvider,
    OpenAICompatibleProvider,
    get_provider,
    parse_llm_response,
)
from manim_studio.editor.prompts import build_user_prompt


class MockProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = MockProvider()
        self.ir = default_ir()

    def test_faster_scales_times(self):
        proposal = self.provider.propose("hazlo más rápido", self.ir)
        self.assertIn("beats", proposal.patch)
        self.assertLess(proposal.patch["beats"][0]["t_anim"], self.ir["beats"][0]["t_anim"])

    def test_format(self):
        proposal = self.provider.propose("cámbialo a 9:16", self.ir)
        self.assertEqual(proposal.patch["format"], "9:16")

    def test_iterations(self):
        proposal = self.provider.propose("usa 3 iteraciones", self.ir)
        self.assertEqual(proposal.patch["params"]["max_iterations"], 3)
        patched = merge_patch(self.ir, proposal.patch)
        self.assertEqual(patched["params"]["max_iterations"], 3)

    def test_function(self):
        proposal = self.provider.propose("f(x) = exp(x) - 2", self.ir)
        self.assertEqual(proposal.patch["function"]["python"], "exp(x) - 2")

    def test_unknown_message(self):
        proposal = self.provider.propose("hola", self.ir)
        self.assertEqual(proposal.patch, {})
        self.assertTrue(proposal.reply)


class ResponseParsingTests(unittest.TestCase):
    def test_parsea_bloque_json(self):
        data = parse_llm_response('```json\n{"reply": "listo", "patch": {}}\n```')
        self.assertEqual(data["reply"], "listo")

    def test_rechaza_texto_sin_json(self):
        with self.assertRaises(LLMError):
            parse_llm_response("lo siento, no puedo")


class OpenAICompatibleProviderTests(unittest.TestCase):
    def setUp(self):
        self.ir = default_ir()
        self.provider = OpenAICompatibleProvider(
            base_url="https://example.test/v1",
            model="test-model",
            api_key="secret",
            timeout=1,
        )

    def _opener(self, body: bytes, status: int = 200):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = body
        opener = MagicMock(return_value=response)
        return opener, response

    def test_respuesta_valida(self):
        content = json.dumps({"reply": "Listo.", "summary": ["ritmo"], "patch": {"format": "1:1"}})
        body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
        opener, _ = self._opener(body)
        self.provider._opener = opener

        proposal = self.provider.propose("cuadrado", self.ir)

        self.assertEqual(proposal.patch, {"format": "1:1"})
        self.assertEqual(proposal.summary, ["ritmo"])
        request = opener.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer secret")
        self.assertIn("/chat/completions", request.full_url)

    def test_json_invalido_levanta_llmerror(self):
        body = json.dumps({"choices": [{"message": {"content": "no es json"}}]}).encode("utf-8")
        opener, _ = self._opener(body)
        self.provider._opener = opener
        with self.assertRaises(LLMError):
            self.provider.propose("algo", self.ir)

    def test_error_http_levanta_llmerror(self):
        response = MagicMock()
        response.read.return_value = b'{"error": "bad key"}'
        error = urllib.error.HTTPError("https://example.test", 401, "Unauthorized", {}, response)
        opener = MagicMock(side_effect=error)
        self.provider._opener = opener
        with self.assertRaises(LLMError):
            self.provider.propose("algo", self.ir)

    def test_reintento_sin_response_format(self):
        body = json.dumps({
            "choices": [{"message": {"content": '{"reply": "Ok", "patch": {}}'}}]
        }).encode("utf-8")
        failing = MagicMock()
        failing.__enter__.side_effect = urllib.error.HTTPError(
            "https://example.test", 400, "Bad Request", {}, MagicMock()
        )
        good = MagicMock()
        good.__enter__.return_value.read.return_value = body
        self.provider._opener = MagicMock(side_effect=[failing, good])

        proposal = self.provider.propose("algo", self.ir)

        self.assertEqual(proposal.reply, "Ok")
        second_payload = json.loads(self.provider._opener.call_args.args[0].data)
        self.assertNotIn("response_format", second_payload)

    def test_repair_reenvia_error(self):
        content = json.dumps({"reply": "Corregido", "patch": {"format": "9:16"}})
        body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
        opener, _ = self._opener(body)
        self.provider._opener = opener
        proposal = llm.LLMProposal("mal", {"format": "7:9"})
        result = self.provider.repair(proposal, "formato inválido", "cámbialo", self.ir)
        self.assertEqual(result.patch["format"], "9:16")
        prompt = json.loads(opener.call_args.args[0].data.decode("utf-8"))
        self.assertIn("formato inválido", prompt["messages"][-1]["content"])


class ProviderSelectionTests(unittest.TestCase):
    def test_sin_clave_cae_a_mock(self):
        with patch.object(llm, "LLM_PROVIDER", "openai"), patch.object(llm, "LLM_API_KEY", ""):
            self.assertIsInstance(get_provider(), MockProvider)

    def test_con_clave_crea_openai(self):
        with patch.object(llm, "LLM_PROVIDER", "openai"), patch.object(llm, "LLM_API_KEY", "k"):
            self.assertIsInstance(get_provider(), OpenAICompatibleProvider)


class PromptTests(unittest.TestCase):
    def test_incluye_historial_y_error(self):
        prompt = build_user_prompt(
            "hazlo más lento",
            default_ir(),
            {
                "history": [{"role": "user", "content": "hola"}],
                "last_error": "f(a) y f(b) tienen el mismo signo",
                "focus": "beats",
            },
        )
        self.assertIn("hola", prompt)
        self.assertIn("mismo signo", prompt)
        self.assertIn("beats", prompt)


if __name__ == "__main__":
    unittest.main()
