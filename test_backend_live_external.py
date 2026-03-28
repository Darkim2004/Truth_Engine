import os
import unittest
from pathlib import Path

from dotenv import load_dotenv

# Carica il file .env della root progetto prima di leggere le variabili.
load_dotenv(Path(__file__).resolve().parent / ".env")


class TestBackendLiveExternal(unittest.TestCase):
    def test_live_elabora_completo_with_groq_and_duckduckgo(self):
        """
        Test live end-to-end (senza mock):
        frontend payload -> /elabora_completo -> Groq claims -> DuckDuckGo search -> fetch -> scoring -> verdetto.

        Esecuzione opzionale:
        - imposta RUN_LIVE_E2E=1
        - imposta GROQ_API_KEY valida
        """
        if os.getenv("RUN_LIVE_E2E", "0") != "1":
            self.skipTest("Test live disabilitato. Imposta RUN_LIVE_E2E=1 per abilitarlo.")

        if not os.getenv("GROQ_API_KEY"):
            self.skipTest("Manca GROQ_API_KEY: impossibile eseguire il test live.")

        # Import locale per evitare side effects durante test discovery.
        import app as app_module

        client = app_module.app.test_client()
        test_text = os.getenv(
            "LIVE_E2E_TEXT",
            (
                "Nel 2025 l'inflazione italiana e calata sotto il 2% secondo dati ufficiali "
                "e alcuni articoli online sostengono il contrario in modo allarmista."
            ),
        )

        response = client.post(
            "/elabora_completo",
            json={
                "mode": "testo",
                "data": test_text,
            },
        )

        # Se il backend ritorna errore, includiamo payload per debug rapido.
        payload = response.get_json(silent=True) or {}
        self.assertEqual(
            response.status_code,
            200,
            msg=f"Status inatteso: {response.status_code}, payload: {payload}",
        )

        self.assertIsInstance(payload, dict)
        self.assertIn("affidabilita", payload)
        self.assertIn("verdetto", payload)
        self.assertIn("fonti", payload)
        self.assertIn("dettagli", payload)

        self.assertIsInstance(payload["affidabilita"], (int, float))
        self.assertGreaterEqual(payload["affidabilita"], 0)
        self.assertLessEqual(payload["affidabilita"], 100)

        self.assertIsInstance(payload["verdetto"], str)
        self.assertTrue(payload["verdetto"].strip())

        self.assertIsInstance(payload["fonti"], list)
        self.assertIsInstance(payload["dettagli"], dict)

        # Questo campo ci conferma che almeno un claim e stato elaborato a valle di Groq.
        claims_analizzati = payload["dettagli"].get("claims_analizzati", 0)
        self.assertGreaterEqual(claims_analizzati, 1)


if __name__ == "__main__":
    unittest.main()
