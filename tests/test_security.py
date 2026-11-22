import unittest

from app.security import (
    UnsafePathError,
    ensure_token,
    normalize_origin,
    origin_is_allowed,
    safe_join,
    token_matches,
)


class SafeJoinTests(unittest.TestCase):
    def setUp(self):
        self.base = "D:/Proyectos/Agente_manim"

    def test_accepts_nested_path(self):
        result = safe_join(self.base, "web/app.js")
        self.assertTrue(str(result).endswith("web\\app.js") or str(result).endswith("web/app.js"))

    def test_rejects_parent_traversal(self):
        with self.assertRaises(UnsafePathError):
            safe_join(self.base, "../server.py")

    def test_rejects_windows_traversal(self):
        with self.assertRaises(UnsafePathError):
            safe_join(self.base, "..\\server.py")

    def test_rejects_absolute_path(self):
        with self.assertRaises(UnsafePathError):
            safe_join(self.base, "C:/Windows/System32/drivers/etc/hosts")

    def test_accepts_base_itself(self):
        self.assertEqual(str(safe_join(self.base, "")), str(safe_join(self.base, "")))


class TokenTests(unittest.TestCase):
    def test_creates_and_reuses_token(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session_token"
            first = ensure_token(path)
            second = ensure_token(path)
            self.assertEqual(first, second)
            self.assertTrue(len(first) >= 20)

    def test_token_compare(self):
        self.assertTrue(token_matches("abc", "abc"))
        self.assertFalse(token_matches("abc", "abd"))
        self.assertFalse(token_matches("abc", None))


class OriginTests(unittest.TestCase):
    def test_normalize_origin(self):
        self.assertEqual(
            normalize_origin("http://127.0.0.1:5000/editor?x=1"),
            "http://127.0.0.1:5000",
        )

    def test_origin_allowlist(self):
        allowed = {"http://127.0.0.1:5000", "http://localhost:5000"}
        self.assertTrue(origin_is_allowed("http://localhost:5000", allowed))
        self.assertFalse(origin_is_allowed("https://evil.example", allowed))
        self.assertTrue(origin_is_allowed(None, allowed))


if __name__ == "__main__":
    unittest.main()
