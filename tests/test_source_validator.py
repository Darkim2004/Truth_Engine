import unittest
from unittest.mock import patch

from core.source_validator import validate_evidence


class TestSourceValidator(unittest.TestCase):
    def test_legacy_validator_wraps_semantic_scoring(self):
        semantic_result = {
            "max_similarity": 0.75,
            "supports_claim": True,
            "matches": [{"chunk_text": "Evidenza rilevante"}],
        }

        with patch(
            "core.source_validator.validate_semantic_evidence",
            return_value=semantic_result,
        ):
            result = validate_evidence(
                "https://www.ansa.it/economia/notizia",
                "Testo fonte",
                "Claim",
            )

        self.assertEqual(result["domain"], "ansa.it")
        self.assertEqual(result["source_score"], 0.9)
        self.assertEqual(result["semantic_relevance"], 0.75)
        self.assertEqual(result["category"], "ATTINENTE")
        self.assertIn("semantic_analysis", result)


if __name__ == "__main__":
    unittest.main()
