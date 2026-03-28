import os
import json
from groq import Groq # <--- Usiamo la libreria Groq per la tua chiave gsk_
from dotenv import load_dotenv

load_dotenv()

# Inizializziamo il client Groq
# Assicurati che nel .env ci sia GROK_API_KEY=gsk_...
client = Groq(api_key=os.getenv("GROK_API_KEY"))

def analyze_context_match(text, claim):
    prompt = f"""
    Analizza il rapporto tra TESTO e CLAIM.
    TESTO: {text}
    CLAIM: {claim}
    Rispondi ESCLUSIVAMENTE con un JSON:
    {{
        "rilevanza": 0.0-1.0,
        "categoria": "CONFERMA_DIRETTA" | "SMENTITA_DIRETTA" | "PARZIALE" | "NON_RILEVANTE",
        "motivazione": "breve spiegazione"
    }}
    """
    try:
        # Chiamata corretta per Groq
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", # Il modello più forte di Groq
            response_format={"type": "json_object"} # Forza l'output in JSON
        )
        
        # Estraiamo il testo della risposta
        return json.loads(chat_completion.choices[0].message.content)
    
    except Exception as e:
        # Stampiamo l'errore nel terminale così capiamo se la chiave scade o altro
        print(f"ERRORE API: {e}")
        return {
            "rilevanza": 0.0, 
            "categoria": "NON_RILEVANTE", 
            "motivazione": f"Errore tecnico: {str(e)}"
        }

def get_final_verdict_logic(evidence_list):
    # Questa sarà la Fase 4: il Giudice Supremo
    pass