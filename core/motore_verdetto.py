import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROK_API_KEY"))

def genera_verdetto_probabilistico(claim, dossier_arricchito):
    """
    Giudice Supremo: Analizza il dossier, esegue cross-check e seleziona i top URL.
    """
    
    prompt = f"""
    Sei un Esperto di Intelligence Forense. Analizza il CLAIM basandoti sul DOSSIER.
    
    CLAIM: {claim}
    DOSSIER: {json.dumps(dossier_arricchito, indent=2)}

    ISTRUZIONI DI ANALISI (CRITICHE):
    1. COERENZA TEMPORALE: Una smentita del 2026 deve avere prove verificabili. Se un dato del 2022 è supportato da fonti .gov/.edu e la smentita del 2026 è vaga, dai priorità alla qualità scientifica.
    2. CROSS-CHECK: Verifica se le fonti citano studi o enti. Se un blog cita l'OMS ma i dati ufficiali nel dossier dicono l'opposto, segnala la manipolazione.
    3. SENTIMENT: Se il testo è troppo aggressivo o allarmista, aumenta il punteggio di Falsità/Incertezza.
    4. SELEZIONE TOP URL: Scegli fino a 3 URL 'supporting' (che confermano il verdetto) e fino a 3 'conflicting' (voci discordanti). Usa solo URL REALI dal dossier.

    RISPONDI ESCLUSIVAMENTE IN JSON:
    {{
        "percentages": {{ 
            "truth": 0, 
            "falsity": 0, 
            "uncertainty": 0 
        }},
        "verdict_label": "VERIFICATO | PARZIALMENTE_VERO | DUBBIO | DISINFORMAZIONE",
        "explainability": {{
            "summary": "Sintesi estrema per l'utente",
            "cross_check_result": "Risultato del confronto tra citazioni e fonti ufficiali",
            "strength_analysis": "Analisi della prova più solida",
            "consensus_level": "Alto/Medio/Basso",
            "next_step": "Cosa cercare per conferma definitiva"
        }},
        "top_sources": {{
            "supporting": [
                {{ "url": "URL_REALE", "reason": "Perché conferma?", "title": "Titolo" }}
            ],
            "conflicting": [
                {{ "url": "URL_REALE", "reason": "Perché smentisce?", "title": "Titolo" }}
            ]
        }},
        "analysis_tags": ["Allarmismo", "Fake Authority", "Dati Scientifici"]
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        # Parsiamo la risposta dell'IA
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e), "status": "failed"}