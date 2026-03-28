import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from models import ArticleMetadata, FetchedPage, SearchResult


def _fake_groq_response(payload: dict) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(payload, ensure_ascii=False))
            )
        ]
    )


class _FakeGroqClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Step 1 in app.py: claim extraction from user text.
        claims_payload = {
            "claims": [
                {
                    "id": 0,
                    "claim_text": "Il dato ufficiale ISTAT smentisce il titolo allarmista",
                    "search_query": "ISTAT comunicato ufficiale dato economia",
                    "category": "economy",
                }
            ]
        }
        return _fake_groq_response(claims_payload)


class TestBackendEndToEnd(unittest.TestCase):
    def test_elabora_completo_full_backend_flow(self):
        # Import locale per evitare side effects all'import del modulo nel test discovery.
        import app as app_module

        captured_dossiers: list[list[dict]] = []

        async def fake_search_duckduckgo(query: str, max_results: int = 2):
            # Include duplicate URL to verify dedup in aggregate_search.
            return [
                SearchResult(
                    url="https://www.ansa.it/economia/notizie/2026/fonte-affidabile.html",
                    title="ANSA Economia",
                    snippet="Fonte istituzionale",
                    source_engine="duckduckgo",
                ),
                SearchResult(
                    url="https://www.ansa.it/economia/notizie/2026/fonte-affidabile.html?utm_source=test",
                    title="ANSA Economia Duplicate",
                    snippet="Duplicato con tracking params",
                    source_engine="duckduckgo",
                ),
                SearchResult(
                    url="https://www.bufale.net/notizia-allarmista",
                    title="Blog allarmista",
                    snippet="Versione manipolata",
                    source_engine="duckduckgo",
                ),
            ]

        async def fake_fetch_batch(urls: list[str]):
            pages = []
            for url in urls:
                if "ansa.it" in url:
                    html = "<html><head><title>ANSA - Dati ufficiali</title></head><body>Dati ufficiali confermano la smentita.</body></html>"
                else:
                    html = "<html><head><title>Blog allarmista</title></head><body>Testo emotivo senza fonti.</body></html>"

                pages.append(
                    FetchedPage(
                        url=url,
                        html=html,
                        status_code=200,
                        fetch_method="httpx",
                        is_valid=True,
                        error="",
                    )
                )
            return pages

        async def fake_close_browser():
            return None

        def fake_extract_article_text(html: str):
            if "ANSA" in html:
                return "Analisi ufficiale: nessuna evidenza di rischio. Dati ISTAT e ministeriali coerenti."
            return "Articolo allarmista privo di riferimenti verificabili."

        def fake_extract_metadata(html: str):
            if "ANSA" in html:
                return ArticleMetadata(
                    title="ANSA - Dati ufficiali",
                    author="Redazione ANSA",
                    description="Report con dati ufficiali",
                    site_name="ANSA",
                )
            return ArticleMetadata(
                title="Blog allarmista",
                author="Anonimo",
                description="Post sensazionalistico",
                site_name="Bufale.net",
            )

        def fake_similarity_validate(url: str, text: str, claim: str, **kwargs):
            if "ansa.it" in url:
                max_similarity = 0.91
                supports = True
                chunk = "Fonte affidabile con evidenza diretta"
            else:
                max_similarity = 0.08
                supports = False
                chunk = "Contenuto non rilevante o manipolato"

            return {
                "url": url,
                "original_text": text,
                "claim": claim,
                "chunks": [text],
                "chunk_similarity_scores": [max_similarity],
                "top_chunk_indices": [0] if supports else [],
                "matches": [
                    {
                        "url": url,
                        "chunk_index": 0,
                        "chunk_text": chunk,
                        "similarity_score": max_similarity,
                    }
                ]
                if supports
                else [],
                "max_similarity": max_similarity,
                "supports_claim": supports,
                "threshold": 0.2,
            }

        def fake_verdict_engine(claim: str, dossier_arricchito: list[dict]):
            captured_dossiers.append(dossier_arricchito)

            supporting = []
            conflicting = []
            for row in dossier_arricchito:
                metadata = row.get("metadata", {})
                title = metadata.get("title") or metadata.get("site_name") or "Fonte"
                entry = {
                    "url": row.get("url", ""),
                    "reason": (
                        f"score_fonte={row.get('score_fonte', 0):.2f}, "
                        f"similarity={row.get('max_similarity', 0):.2f}"
                    ),
                    "title": title,
                }
                if row.get("supports_claim_math") and row.get("score_fonte", 0) >= 0.8:
                    supporting.append(entry)
                else:
                    conflicting.append(entry)

            return {
                "percentages": {"truth": 82, "falsity": 10, "uncertainty": 8},
                "verdict_label": "VERIFICATO",
                "explainability": {
                    "summary": "Le fonti affidabili prevalgono sulle fonti allarmiste.",
                    "cross_check_result": "Coerenza elevata tra fonti autorevoli.",
                    "strength_analysis": "Dati ANSA coerenti con fonti istituzionali.",
                    "consensus_level": "Alto",
                    "next_step": "Monitorare aggiornamenti ufficiali.",
                },
                "top_sources": {
                    "supporting": supporting[:3],
                    "conflicting": conflicting[:3],
                },
                "analysis_tags": ["Dati Scientifici", "Cross-Check"],
            }

        with (
            patch("groq.Groq", _FakeGroqClient),
            patch("search.duckduckgo.search_duckduckgo", side_effect=fake_search_duckduckgo),
            patch("pipeline.fetch_batch", side_effect=fake_fetch_batch),
            patch("pipeline.close_browser", side_effect=fake_close_browser),
            patch("pipeline.is_paywall", return_value=False),
            patch("pipeline.is_correct_language", return_value=True),
            patch("pipeline.detect_language", return_value="it"),
            patch("pipeline.extract_article_text", side_effect=fake_extract_article_text),
            patch("pipeline.extract_metadata", side_effect=fake_extract_metadata),
            patch("pipeline.validate_evidence", side_effect=fake_similarity_validate),
            patch("core.engine.validate_evidence", side_effect=fake_similarity_validate),
            patch("core.engine.genera_verdetto_probabilistico", side_effect=fake_verdict_engine),
        ):
            client = app_module.app.test_client()
            response = client.post(
                "/elabora_completo",
                json={
                    "mode": "testo",
                    "data": "Titolo allarmista: i dati ufficiali sarebbero falsi",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        # Assert output frontend-oriented mapping.
        self.assertEqual(payload["verdetto"], "Informazione verificata")
        self.assertEqual(payload["affidabilita"], 82)
        self.assertIn("fonti", payload)
        self.assertGreaterEqual(len(payload["fonti"]), 2)

        output_urls = [f.get("url", "") for f in payload["fonti"]]
        self.assertTrue(any("ansa.it" in url for url in output_urls))
        self.assertTrue(any("bufale.net" in url for url in output_urls))

        # Assert source classification happened in dossier (credibility + relevance).
        self.assertEqual(len(captured_dossiers), 1)
        dossier = captured_dossiers[0]
        self.assertGreaterEqual(len(dossier), 2)

        ansa_row = next(row for row in dossier if "ansa.it" in row["url"])
        bufale_row = next(row for row in dossier if "bufale.net" in row["url"])

        self.assertGreaterEqual(ansa_row["score_fonte"], 0.9)
        self.assertTrue(ansa_row["supports_claim_math"])

        self.assertLessEqual(bufale_row["score_fonte"], 0.2)
        self.assertFalse(bufale_row["supports_claim_math"])


if __name__ == "__main__":
    unittest.main()
