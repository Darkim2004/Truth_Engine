import unittest

from core.motore_verdetto import genera_verdetto_probabilistico


class TestVerdictEngine(unittest.TestCase):
    def test_verdict_uses_weighted_confirming_and_conflicting_chunks(self):
        dossier = [
            {
                "url": "https://www.ansa.it/salute/fonte-affidabile",
                "score_fonte": 0.9,
                "chunks_analizzati": [
                    {
                        "categoria": "CONFUTA",
                        "motivazione": "La fonte autorevole smentisce il claim.",
                    }
                ],
            },
            {
                "url": "https://verita-nascoste-blog.it/post",
                "score_fonte": 0.2,
                "chunks_analizzati": [
                    {
                        "categoria": "CONFERMA",
                        "motivazione": "La fonte debole sostiene il claim.",
                    }
                ],
            },
        ]

        result = genera_verdetto_probabilistico("Claim di prova", dossier)

        self.assertEqual(result["verdict_label"], "DISINFORMAZIONE")
        self.assertGreater(result["percentages"]["falsity"], result["percentages"]["truth"])
        self.assertEqual(len(result["top_sources"]["supporting"]), 1)
        self.assertEqual(len(result["top_sources"]["conflicting"]), 1)


if __name__ == "__main__":
    unittest.main()
