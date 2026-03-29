import requests
import json
import os

def pull_mbfc_data():
    # URL del database MBFC aggiornato alla corretta path su main
    MBFC_URL = "https://raw.githubusercontent.com/drmikecrowe/mbfcext/main/docs/sources.json"
    
    print("Obiettivo: Pulling dati da MBFC...")
    
    try:
        response = requests.get(MBFC_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        nuova_libreria = {}
        
        for domain, info in data.items():
            # Filtriamo solo le fonti affidabili (High o Very High)
            # MBFC usa 'reporting' per il livello di accuratezza dei fatti
            reporting_level = str(info.get('reporting', '')).lower()
            
            if "high" in reporting_level or "very high" in reporting_level:
                nuova_libreria[domain] = {
                    "score": 1.0 if "very high" in reporting_level else 0.8,
                    "label": f"MBFC {reporting_level.capitalize()}",
                    "category": info.get('bias', 'General News')
                }
            elif "low" in reporting_level:
                # Se vuoi pullare anche la "Blacklist"
                nuova_libreria[domain] = {
                    "score": 0.1,
                    "label": "MBFC Low Factual",
                    "category": "Disinformation"
                }

        # Salvataggio nel file
        out_path = os.path.join(os.path.dirname(__file__), 'database_affidabilita.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(nuova_libreria, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Successo! Importati {len(nuova_libreria)} domini verificati in {out_path}.")

    except Exception as e:
        print(f"❌ Errore durante il pull: {e}")

if __name__ == "__main__":
    pull_mbfc_data()
