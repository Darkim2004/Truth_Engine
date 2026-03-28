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
    Sei un Esperto di Intelligence e Fact-Checking. 
    Analizza il CLAIM e valuta le EVIDENZE fornite, pesando i METADATI (data, autore, citazioni).

    CLAIM: {claim}
    
    EVIDENZE (Dossier):
    {json.dumps(dossier_arricchito, indent=2)}

    ISTRUZIONI DI ANALISI:
    1. COERENZA TEMPORALE E QUALITÀ: Non dare priorità alla data in modo assoluto. Valuta se la smentita recente (2026) porta nuove prove verificabili o se è solo un'opinione. Se un'evidenza del 2022 è supportata da dati numerici e fonti .gov, e la smentita del 2026 è vaga, mantieni un Truth Score alto ma segnala l'anomalia nell'Uncertainty.
    2. AUTOREVOLEZZA: Un autore noto o un sito .gov/.edu ha peso triplo rispetto a un blog anonimo.
    3. TRASPARENZA: Se il metadato 'has_citations' è true, aumenta la fiducia (Truth Score).
    4. SENTIMENT: Se il testo è troppo emotivo/aggressivo, aumenta l'Uncertainty o il False Score.

    RISPONDI ESCLUSIVAMENTE IN JSON:
    {{
        "percentages": {{
            "truth": 0-100,
            "falsity": 0-100,
            "uncertainty": 0-100
        }},
        "verdict_label": "APPROVATO | PARZIALMENTE_VERO | DUBBIO | DISINFORMAZIONE",
        "explainability": {{
            "summary": "Sintesi in una riga per l'utente",
            "strength_analysis": "Analisi della fonte più solida (es. dati .gov del 2022)",
            "conflict_details": "Spiegazione del perché esiste incertezza (es. discrepanza tra dati 2022 e opinioni 2026)",
            "consensus_level": "Alto/Medio/Basso - indica se le fonti autorevoli sono d'accordo tra loro",
            "next_step": "Cosa dovrebbe cercare l'utente per avere la certezza assoluta"
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