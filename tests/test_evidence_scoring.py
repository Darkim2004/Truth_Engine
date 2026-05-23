import unittest
from unittest.mock import patch

import numpy as np

from scoring.paragraph_chunker import chunk_by_paragraphs
from scoring.evidence_matcher import validate_evidence


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
    def test_validate_evidence_shape(self):
        claim = "Il vaccino causa autismo"
        url = "https://example.com/article-1"
        text = "I vaccini non causano autismo secondo molte revisioni scientifiche."

        with (
            patch("scoring.evidence_matcher.embed_texts") as mock_embed_texts,
            patch("scoring.evidence_matcher.compute_similarity") as mock_similarity,
        ):
            mock_embed_texts.return_value = np.array([[1.0, 0.0]])
            mock_similarity.return_value = np.array([0.83])

            results = validate_evidence(url=url, text=text, claim=claim, min_threshold=0.2, top_k=3)

        self.assertEqual(results["url"], url)
        self.assertIn("chunks", results)
        self.assertIn("chunk_similarity_scores", results)
        self.assertIn("top_chunk_indices", results)
        self.assertIn("matches", results)



if __name__ == "__main__":
    unittest.main()
