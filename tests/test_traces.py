import unittest
from cobble.traces import mint_trace_uri


class TraceTests(unittest.TestCase):
    def test_minted_uris_are_distinct(self):
        first = mint_trace_uri()
        second = mint_trace_uri()

        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("https://cobble.link/t/"))
