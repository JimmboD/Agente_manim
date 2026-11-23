import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from manim_studio.editor import llm
from manim_studio.editor.llm import (
    LLMError,
    MockProvider,
    OpenAICompatibleProvider,
    get_provider,
    parse_llm_response,
)


class ResponseParsingTests(unittest.TestCase):
    def test_parsea_bloque_json(self):
        data = parse_llm_response('```json\n{"reply": "listo", "code": "x = 1"}\n```')
        self.assertEqual(data["code"], "x = 1")

    def test_rechaza_texto_sin_json(self):
        with self.assertRaises(LLMError):
            parse_llm_response("lo siento, no puedo")


class OpenAICompatibleProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = OpenAICompatibleProvider(
            base_url="https://example.test/v1",
            model="test-model",
            api_key="secret",
            timeout=1,
        )

    def _opener(self, body: bytes):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = body
        return MagicMock(return_value=response)

    def test_chat_json_devuelve_contenido(self):
        content = json.dumps({"reply": "Listo.", "code": "x = 1"})
        body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
        opener = self._opener(body)
        self.provider._opener = opener

        raw = self.provider.chat_json([{"role": "user", "content": "hola"}])

        self.assertEqual(json.loads(raw)["code"], "x = 1")
        request = opener.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer secret")
        self.assertIn("/chat/completions", request.full_url)
        payload = json.loads(request.data)
        self.assertEqual(payload["response_format"], {"type": "json_object"})

    def test_json_invalido_levanta_llmerror(self):
        body = json.dumps({"choices": [{"message": {"content": "no es json"}}]}).encode("utf-8")
        self.provider._opener = self._opener(body)
        with self.assertRaises(LLMError):
            parse_llm_response(self.provider.chat_json([]))

    def test_error_http_levanta_llmerror(self):
        response = MagicMock()
        response.read.return_value = b'{"error": "bad key"}'
        error = urllib.error.HTTPError("https://example.test", 401, "Unauthorized", {}, response)
        self.provider._opener = MagicMock(side_effect=error)
        with self.assertRaises(LLMError):
            self.provider.chat_json([])

    def test_reintento_sin_response_format(self):
        body = json.dumps({
            "choices": [{"message": {"content": '{"reply": "Ok"}'}}]
        }).encode("utf-8")
        failing = MagicMock()
        failing.__enter__.side_effect = urllib.error.HTTPError(
            "https://example.test", 400, "Bad Request", {}, MagicMock()
        )
        good = MagicMock()
        good.__enter__.return_value.read.return_value = body
        self.provider._opener = MagicMock(side_effect=[failing, good])

        self.provider.chat_json([])

        second_payload = json.loads(self.provider._opener.call_args.args[0].data)
        self.assertNotIn("response_format", second_payload)


class ProviderSelectionTests(unittest.TestCase):
    def test_sin_clave_cae_a_mock(self):
        with patch.object(llm, "LLM_PROVIDER", "openai"), patch.object(llm, "LLM_API_KEY", ""):
            self.assertIsInstance(get_provider(), MockProvider)

    def test_con_clave_crea_openai(self):
        with patch.object(llm, "LLM_PROVIDER", "openai"), patch.object(llm, "LLM_API_KEY", "k"):
            self.assertIsInstance(get_provider(), OpenAICompatibleProvider)


if __name__ == "__main__":
    unittest.main()
