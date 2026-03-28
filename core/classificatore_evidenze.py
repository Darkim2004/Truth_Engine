import os
import json
import google.generativeai as genai
from dotenv import load_dotenv # <--- Importa la libreria

# Carica le variabili dal file .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configura Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

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
        response = model.generate_content(prompt)
        return json.loads(response.text.strip('`json\n '))
    except:
        return {"rilevanza": 0.5, "categoria": "NON_RILEVANTE", "motivazione": "Errore API"}

# Se vuoi essere super ordinato, aggiungi anche questa per il source_validator
def get_final_verdict_logic(evidence_list):
    # Qui andrà la logica della FASE 4
    pass