import sys
from pathlib import Path

# Questo trova la cartella "padre" (Truth_Engine) e la aggiunge ai percorsi di Python
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

# ORA puoi importare core senza errori
import json
from core.motore_verdetto import genera_verdetto_probabilistico


# Simuliamo quello che Andrea dovrebbe passarti dopo la Fase 3
claim_test = "Il consumo di farina di grillo causa alterazioni del DNA umano"

dossier_fake = [
    {
        "url": "https://scienza-ufficiale.it/studio-genetica",
        "text": "Non esiste alcuna prova scientifica che le proteine degli insetti interagiscano con il DNA umano.",
        "metadata": {
            "date": "2026-01-15",
            "author": "Dr. Elena Bianchi (Genetista)",
            "site_trust_score": 0.95,
            "has_citations": True
        },
        "ai_analysis": {"categoria": "SMENTITA_DIRETTA", "rilevanza": 0.98}
    },
    {
        "url": "https://verita-nascoste.blog",
        "text": "Mio cugino dice che dopo aver mangiato grilli ha iniziato a sentirsi strano. Sveglia!!1!",
        "metadata": {
            "date": "2022-05-10",
            "author": "Anonimo",
            "site_trust_score": 0.2,
            "has_citations": False
        },
        "ai_analysis": {"categoria": "CONFERMA_DIRETTA", "rilevanza": 0.4}
    }
]

print("--- GENERAZIONE VERDETTO IN CORSO ---")
risultato = genera_verdetto_probabilistico(claim_test, dossier_fake)
print(json.dumps(risultato, indent=2))