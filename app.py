from flask import Flask, request, jsonify
from flask_cors import CORS
from core.engine import truth_engine_main
import json


app = Flask(__name__)
# Permette la comunicazione col tuo Frontend
CORS(app) 

@app.route('/api/verify', methods=['POST'])
def verify():
    """
    Questa è la porta d'ingresso per Matteo.
    Lui ti manda un JSON con { "claim": "...", "results": [...] }
    """
    data = request.json
    if not data:
        return jsonify({"error": "Nessun dato ricevuto"}), 400
    
    claim = data.get('claim')
    search_results = data.get('results', [])

    # Chiamiamo il tuo motore che abbiamo pulito prima
    # Lui processa i pesi, i chunk di Andrea e chiede a Groq
    verdetto = truth_engine_main(claim, search_results)

    # Restituiamo il JSON finale che Matteo userà per la UI
    return jsonify(verdetto)

if __name__ == '__main__':
    # Avvia il server sulla porta 5000
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/elabora', methods=['POST'])
def elabora():
    # Riceve il JSON dal tuo Frontend
    dati_ricevuti = request.json
    
    # OPZIONALE: Se Andrea vuole proprio scrivere il file fisico:
    with open('input.json', 'w') as f:
        json.dump(dati_ricevuti, f, indent=4)

    # --- QUI ANDREA FA LA SUA MAGIA ---
    # Esempio: lui cerca su Google, confronta i dati, ecc.
    # Se la pipeline (LLM + scarping) è pronta, qui la richiameremo così:
    # import asyncio
    # from pipeline import run_pipeline
    # output = asyncio.run(run_pipeline(dati_ricevuti))
    # risultato = output.model_dump()
    
    # Dati mock attualmente richiesti
    risultato = {
        "verdetto": "Inaffidabile",
        "confidenza": "85%",
        "fonti_trovate": 2
    }
    
    # Restituisce il risultato al Frontend
    return jsonify(risultato)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
