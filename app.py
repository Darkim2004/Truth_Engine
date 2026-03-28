import json
import requests
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import dei moduli del tuo team
from core.engine import truth_engine_main
from extractor.metadata import extract_metadata

# Carichiamo le variabili d'ambiente (.env)
load_dotenv()

app = Flask(__name__)

# Configurazione CORS "Blindata" per evitare errori Load Failed su Safari
CORS(app, resources={r"/*": {"origins": "*"}})

# --- ROTTA 1: VERIFICA COMPLETA (Il motore di Andrea/Luigi) ---
@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    if not data:
        return jsonify({"error": "Nessun dato ricevuto"}), 400
    
    claim = data.get('claim')
    search_results = data.get('results', [])

    # Chiamiamo il motore core
    verdetto = truth_engine_main(claim, search_results)
    return jsonify(verdetto)

# --- ROTTA 2: ELABORA (La funzione per Matteo e la UI) ---
@app.route('/elabora', methods=['POST', 'OPTIONS'])
def elabora():
    # Gestione automatica del pre-flight del browser
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    payload = request.json
    if not payload:
        return jsonify({"error": "Payload mancante"}), 400

    mode = payload.get('mode') # 'testo' o 'url'
    input_data = payload.get('data')
    
    data_to_analyze = ""
    data_to_save = {}

    if mode == 'url':
        try:
            # Scarichiamo la pagina con un User-Agent per evitare blocchi
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            res = requests.get(input_data, timeout=10, headers=headers)
            res.raise_for_status()
            
            # Estrazione metadata
            metadata = extract_metadata(res.text)
            
            data_to_analyze = f"Titolo: {metadata.title}. Descrizione: {metadata.description}. Autore: {metadata.author}"
            data_to_save = {
                "tipo": "URL",
                "url": input_data,
                "metadata": {
                    "titolo": metadata.title,
                    "descrizione": metadata.description,
                    "autore": metadata.author,
                    "sito": metadata.site_name
                }
            }
        except Exception as e:
            print(f"❌ Errore URL: {e}")
            return jsonify({"error": f"Errore durante l'estrazione URL: {str(e)}"}), 400
    else:
        # Modalità Testo Libero
        data_to_analyze = input_data
        data_to_save = {
            "tipo": "TESTO",
            "contenuto": input_data
        }

    # --- SCRITTURA SU FILE input.json ---
    try:
        with open('input.json', 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        print("✅ input.json aggiornato correttamente.")
    except Exception as e:
        print(f"❌ Errore salvataggio file: {e}")

    return jsonify({
        "status": "success",
        "testo_estratto": data_to_analyze
    })

# --- AVVIO DEL SERVER (SOSTITUISCI IL FINALE) ---
if __name__ == '__main__':
    # Usiamo 127.0.0.1 invece di 0.0.0.0 per essere "amici" di Safari
    print("🚀 Truth Shield Server attivo su http://127.0.0.1:5001")
    app.run(host='127.0.0.1', port=5001, debug=True)