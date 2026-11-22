import unittest

from app.ir import default_ir, merge_patch
from app.llm import MockProvider


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


if __name__ == "__main__":
    unittest.main()
