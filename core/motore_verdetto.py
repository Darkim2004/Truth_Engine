import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROK_API_KEY"))

def genera_verdetto_probabilistico(claim, dossier_arricchito):
    """
    Analizza il claim basandosi su un dossier pieno di metadati.
    """
    
    prompt = f"""
    Sei un Esperto di Intelligence. Analizza il CLAIM e il DOSSIER.
    
    CLAIM: {claim}
    DOSSIER: {json.dumps(dossier_arricchito, indent=2)}

    Oltre alle percentuali, devi SELEZIONARE i top URL:
    - Scegli fino a 3 URL che SUPPORTANO il verdetto finale (le prove più forti).
    - Scegli fino a 3 URL che CONTRADDICONO il verdetto (le "voci fuori dal coro" o fake news).

    RISPONDI IN JSON:
    {{
        "percentages": {{ "truth": 0, "falsity": 0, "uncertainty": 0 }},
        "verdict_label": "...",
        "explainability": {{ ... }},
        "top_sources": {{
            "supporting": [
                {{ "url": "URL", "reason": "Perché è affidabile?", "title": "Titolo breve" }}
            ],
            "conflicting": [
                {{ "url": "URL", "reason": "Perché è in contrasto?", "title": "Titolo breve" }}
            ]
        }}
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e), "status": "failed"}