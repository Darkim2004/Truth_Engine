import os
import json
from groq import Groq # <--- Usiamo la libreria Groq per la tua chiave gsk_
from dotenv import load_dotenv

load_dotenv()

# Inizializziamo il client Groq
# Assicurati che nel .env ci sia GROQ_API_KEY=gsk_...
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_context_match(text, claim):
    prompt = f"""
    Sei un analista imparziale. Analizza il seguente frammento di testo (CHUNK) rispetto all'affermazione iniziale (CLAIM).
    Il tuo UNICO compito è capire se il CHUNK supporta o smentisce il CLAIM.
    
    CHUNK: {text}
    
    CLAIM: {claim}
    
    Rispondi ESCLUSIVAMENTE con un JSON con le seguenti chiavi:
    {{
        "categoria": "CONFERMA" | "CONFUTA" | "NON_ATTINENTE",
        "motivazione": "breve spiegazione della tua scelta in una riga"
    }}
    
    Regole:
    - Scegli "CONFERMA" se il CHUNK contiene informazioni che sostengono il fatto o dimostrano che il CLAIM è vero. (Corrisponde a "non confuta" / supporta).
    - Scegli "CONFUTA" se il CHUNK contiene informazioni che dimostrano che il CLAIM è falso, errato o disinformazione.
    - Scegli "NON_ATTINENTE" se il CHUNK non affronta direttamente il CLAIM, parla di altro, oppure è un boilerplate del sito.
    Non inventare niente, basati solo sulle informazioni presenti nel CHUNK.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        risultato = json.loads(chat_completion.choices[0].message.content)
        # Normalizziamo l'output per evitare errori di case o incomprensioni dell'IA
        cat = risultato.get("categoria", "NON_ATTINENTE").upper()
        if cat not in ["CONFERMA", "CONFUTA", "NON_ATTINENTE"]:
            cat = "NON_ATTINENTE"
        
        return {
            "categoria": cat,
            "motivazione": risultato.get("motivazione", "")
        }
    
    except Exception as e:
        print(f"ERRORE API GROQ: {e}")
        return {
            "categoria": "NON_ATTINENTE", 
            "motivazione": f"Errore tecnico: {str(e)}"
        }