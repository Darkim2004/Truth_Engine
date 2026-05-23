from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_client: Groq | None = None


def get_groq_client() -> Groq:
    """Create the Groq client lazily so imports and test discovery stay cheap."""
    global _client

    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY non configurata.")
        _client = Groq(api_key=api_key)

    return _client


def analyze_context_match(chunks_list: list[str], claim: str) -> list[dict]:
    """
    Classify evidence chunks for a claim with a single batched Groq request.

    Returns one item per input chunk with:
    - categoria: CONFERMA, CONFUTA, or NON_ATTINENTE
    - motivazione: short explanation from the model
    """
    if not chunks_list:
        return []

    chunks_dict = {f"chunk_{i}": text for i, text in enumerate(chunks_list)}
    prompt = f"""
Sei un analista imparziale. Ti fornirò un'affermazione (CLAIM) e una serie di frammenti di testo enumerati.
Il tuo unico compito è classificare se ogni singolo chunk supporta o smentisce il CLAIM.

CLAIM: {claim}

CHUNKS:
{json.dumps(chunks_dict, ensure_ascii=False, indent=2)}

Rispondi esclusivamente con un JSON che contenga una lista "risultati" corrispondente a ogni chunk:
{{
  "risultati": [
    {{
      "id": "chunk_0",
      "categoria": "CONFERMA" | "CONFUTA" | "NON_ATTINENTE",
      "motivazione": "Spiega in 1 riga"
    }}
  ]
}}

Regole:
- CONFERMA se il chunk dimostra che il claim è vero.
- CONFUTA se il chunk dimostra che il claim è falso o errato.
- NON_ATTINENTE se il chunk non risponde in modo netto al claim.
"""
    try:
        chat_completion = get_groq_client().chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
        )

        result = json.loads(chat_completion.choices[0].message.content)
        result_items = result.get("risultati", [])

        classifications = []
        for i in range(len(chunks_list)):
            chunk_id = f"chunk_{i}"
            match = next((item for item in result_items if item.get("id") == chunk_id), None)

            if match:
                category = match.get("categoria", "NON_ATTINENTE").upper()
                if category not in ["CONFERMA", "CONFUTA", "NON_ATTINENTE"]:
                    category = "NON_ATTINENTE"
                classifications.append(
                    {
                        "categoria": category,
                        "motivazione": match.get("motivazione", ""),
                    }
                )
            else:
                classifications.append(
                    {"categoria": "NON_ATTINENTE", "motivazione": "Errore mapping"}
                )

        return classifications

    except Exception as exc:
        print(f"ERRORE API GROQ BATCH: {exc}")
        return [
            {"categoria": "NON_ATTINENTE", "motivazione": f"Errore: {exc}"}
            for _ in chunks_list
        ]
