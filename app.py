import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
# Importiamo dalla cartella extractor il file metadata.py
from extractor.metadata import extract_metadata

app = Flask(__name__)
CORS(app)

@app.route('/elabora', methods=['POST'])
def elabora():
    payload = request.json
    mode = payload.get('mode') # 'testo' o 'url'
    input_data = payload.get('data')
    
    data_to_analyze = ""
    data_to_save = {}

    if mode == 'url':
        try:
            # Scarichiamo la pagina
            res = requests.get(input_data, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            res.raise_for_status()
            
            # Usiamo la funzione di Andrea
            metadata = extract_metadata(res.text)
            
            data_to_analyze = f"Titolo: {metadata.title}. Descrizione: {metadata.description}. Autore: {metadata.author}"
            data_to_save = {
                "tipo": "URL",
                "url": input_data,
                "metadata": {
                    "titolo": metadata.title,
                    "descrizione": metadata.description,
                    "autore": metadata.author
                }
            }
        except Exception as e:
            return jsonify({"error": f"Errore URL: {str(e)}"}), 400
    else:
        # Modalità Testo
        data_to_analyze = input_data
        data_to_save = {
            "tipo": "TESTO",
            "contenuto": input_data
        }

    # --- SCRITTURA SU FILE (Per Andrea) ---
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

if __name__ == '__main__':
    app.run(port=5000, debug=True)