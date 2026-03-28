import os
from dotenv import load_dotenv

load_dotenv()

# Cambia GEMINI con GROK qui!
chiave = os.getenv('GROK_API_KEY')
if chiave:
    print(f"DEBUG: La chiave inizia con: {chiave[:5]}...")
else:
    print("DEBUG: La chiave è NONE! Il file .env non viene letto.")

# 3. Il resto del tuo test
from core.source_validator import validate_evidence

url_test = "https://www.ansa.it"
testo_test = "Il prezzo del gas è calato."
claim_test = "Calo prezzi gas"

risultato = validate_evidence(url_test, testo_test, claim_test)
print(risultato)