import os
import json
from groq import Groq # <--- Usiamo la libreria Groq per la tua chiave gsk_
from dotenv import load_dotenv

load_dotenv()

# Inizializziamo il client Groq
# Assicurati che nel .env ci sia GROQ_API_KEY=gsk_...
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_context_match(chunks_list, claim):
    """
    Analizza una lista di chunk rispetto al claim IN UNA SINGOLA CHIAMATA API (Batch)
    per risparmiare pesantemente sui Tokens Per Day e non incappare nel limite 429.
    """
    if not chunks_list:
        return []

    # Creiamo un dizionario dei chunk per passarli comodamente al LLM
    chunks_dict = {f"chunk_{i}": test for i, test in enumerate(chunks_list)}
    
    prompt = f"""
    Sei un analista imparziale. Ti fornirò un'affermazione (CLAIM) e una serie di frammenti di testo enumerati.
    Il tuo UNICO compito è classificare se ogni singolo chunk supporta o smentisce il CLAIM.
    
    CLAIM: {claim}
    
    CHUNKS:
    {json.dumps(chunks_dict, ensure_ascii=False, indent=2)}
    
    Rispondi ESCLUSIVAMENTE con un JSON che contenga una lista "risultati" corrispondente a ogni chunk:
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
        # Usiamo il modello veloce 8b che ha token pool separato/più alto.
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        
        risultato = json.loads(chat_completion.choices[0].message.content)
        lista_risultati = risultato.get("risultati", [])
        
        # Mappiamo i risultati
        classificazioni = []
        for i in range(len(chunks_list)):
            chunk_id = f"chunk_{i}"
            # Troviamo la risposta corrispondente
            match = next((item for item in lista_risultati if item.get("id") == chunk_id), None)
            
            if match:
                cat = match.get("categoria", "NON_ATTINENTE").upper()
                if cat not in ["CONFERMA", "CONFUTA", "NON_ATTINENTE"]:
                    cat = "NON_ATTINENTE"
                classificazioni.append({
                    "categoria": cat,
                    "motivazione": match.get("motivazione", "")
                })
            else:
                classificazioni.append({"categoria": "NON_ATTINENTE", "motivazione": "Errore mapping"})
                
        return classificazioni
    
    except Exception as e:
        print(f"ERRORE API GROQ BATCH: {e}")
        # In caso di errore restituiamo NON_ATTINENTE per tutti i chunk
        return [{"categoria": "NON_ATTINENTE", "motivazione": f"Errore: {e}"} for _ in chunks_list]