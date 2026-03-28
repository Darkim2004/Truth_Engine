import unittest

from scoring.paragraph_chunker import chunk_by_paragraphs
from scoring.evidence_matcher import processa_tutte_le_fonti


class TestChunking(unittest.TestCase):
    def test_chunk_by_paragraphs_merge_small_and_split_large(self):
        text = (
            "Intro breve.\n\n"
            "Altro mini paragrafo.\n\n"
            + ("Frase molto lunga. " * 120)
        )

        chunks = chunk_by_paragraphs(text, min_chunk_size=60, max_chunk_size=220)

        self.assertTrue(len(chunks) >= 2)
        self.assertTrue(any(len(chunk) <= 220 for chunk in chunks))
        self.assertTrue(all(chunk.strip() for chunk in chunks))


class TestEvidenceAPI(unittest.TestCase):
    def test_processa_tutte_le_fonti_shape(self):
        claim = "Il vaccino causa autismo"
        sources = [
            {
                "url": "https://example.com/article-1",
                "text": "I vaccini non causano autismo secondo molte revisioni scientifiche.",
            },
            {
                "url": "https://example.com/article-2",
                "text": "Articolo di sport senza relazione con il claim.",
            },
        ]

        results = processa_tutte_le_fonti(claim, sources, min_threshold=0.2, top_k=3)

        self.assertEqual(len(results), 2)
        self.assertIn("url", results[0])
        self.assertIn("analisi", results[0])
        self.assertIn("chunks", results[0]["analisi"])
        self.assertIn("chunk_similarity_scores", results[0]["analisi"])
        self.assertIn("top_chunk_indices", results[0]["analisi"])


if __name__ == "__main__":
    unittest.main()
