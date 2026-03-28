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

# --- ROTTA 3: ELABORA COMPLETO (Pipeline reale: Groq claims → DuckDuckGo → Core Engine) ---
@app.route('/elabora_completo', methods=['POST', 'OPTIONS'])
def elabora_completo():
    """
    Flusso completo lato server:
    1. Groq genera claims + search queries dal testo dell'utente
    2. Pipeline: DuckDuckGo → fetch → extract → scoring
    3. Core Engine: verdetto finale
    4. Mapping risultato per la dashboard frontend
    """
    import asyncio
    from groq import Groq
    from pipeline import run_pipeline

    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    payload = request.json
    if not payload:
        return jsonify({"error": "Payload mancante"}), 400

    mode = payload.get('mode')
    input_data = payload.get('data')

    # --- STEP 0: Estrai il testo da analizzare ---
    data_to_analyze = ""
    source_url = ""

    if mode == 'url':
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            res = requests.get(input_data, timeout=10, headers=headers)
            res.raise_for_status()
            metadata = extract_metadata(res.text)
            data_to_analyze = f"Titolo: {metadata.title}. Descrizione: {metadata.description}. Autore: {metadata.author}"
            source_url = input_data
        except Exception as e:
            return jsonify({"error": f"Errore URL: {str(e)}"}), 400
    else:
        data_to_analyze = input_data

    try:
        # --- STEP 1: Groq genera claims e search queries ---
        print(f"🧠 Step 1: Groq genera claims dal testo...")
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sei un analista di fact-checking. Dato un testo, estrai le affermazioni verificabili (claims) e genera per ciascuna una query di ricerca ottimizzata per DuckDuckGo. Rispondi SOLO in JSON."},
                {"role": "user", "content": f"""Analizza questo testo ed estrai le affermazioni da verificare:

"{data_to_analyze}"

Rispondi con un JSON nel formato:
{{
  "claims": [
    {{
      "id": 0,
      "claim_text": "L'affermazione da verificare",
      "search_query": "query ottimizzata per cercare su DuckDuckGo",
      "category": "health/science/politics/economy/other"
    }}
  ]
}}

Estrai massimo 3 claims. Le search_query devono essere in italiano e ottimizzate per trovare fonti che confermino o smentiscano il claim."""}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        claims_data = json.loads(chat_completion.choices[0].message.content)
        claims_list = claims_data.get("claims", [])
        print(f"✅ Groq ha generato {len(claims_list)} claims")

        if not claims_list:
            return jsonify({"error": "Nessun claim estratto dal testo"}), 400

        # --- STEP 2: Costruisci PipelineInput e lancia la pipeline ---
        print(f"🔍 Step 2: Pipeline (DuckDuckGo → fetch → extract → scoring)...")
        pipeline_input = {
            "metadata": {
                "source_type": "user_input",
                "timestamp": "",
                "language": "it"
            },
            "original_source": {
                "text_content": data_to_analyze,
                "url": source_url
            },
            "analysis": {
                "engine": "LLM-Powered",
                "claims_to_verify": claims_list
            }
        }

        # Salva input.json per debug
        with open('input.json', 'w', encoding='utf-8') as f:
            json.dump(pipeline_input, f, indent=4, ensure_ascii=False)

        # Esegui la pipeline di crawling (DuckDuckGo search → fetch → extract → score)
        pipeline_output = asyncio.run(run_pipeline(pipeline_input))
        pipeline_dict = pipeline_output.model_dump()

        print(f"📊 Pipeline completata: {pipeline_dict['total_sources_found']} fonti trovate")

        # --- STEP 3: Core Engine — verdetto per ogni claim ---
        print(f"⚖️ Step 3: Core Engine genera il verdetto finale...")
        verdetti = []
        for result in pipeline_dict.get("results", []):
            claim_text = result["claim"]["claim_text"]
            sources = result.get("sources", [])

            if sources:
                # Prepara i dati per truth_engine_main
                search_results_for_engine = []
                for src in sources:
                    search_results_for_engine.append({
                        "url": src["url"],
                        "text": src.get("article_text", ""),
                        "metadata": src.get("metadata", {})
                    })

                verdetto = truth_engine_main(claim_text, search_results_for_engine)
                verdetti.append({
                    "claim": claim_text,
                    "verdetto": verdetto,
                    "fonti_reali": sources
                })
            else:
                verdetti.append({
                    "claim": claim_text,
                    "verdetto": {"verdict_label": "INCERTO", "percentages": {"truth": 0, "falsity": 0, "uncertainty": 100}},
                    "fonti_reali": []
                })

        # --- STEP 4: Mappatura per il frontend dashboard ---
        print(f"🎨 Step 4: Mapping per la dashboard...")

        # Prendi il verdetto principale (primo claim o media)
        if verdetti:
            main = verdetti[0]["verdetto"]
            percentages = main.get("percentages", {})
            truth_pct = percentages.get("truth", 50)
            label = main.get("verdict_label", "INCERTO")

            # Mappa colore in base al verdetto
            colore_map = {
                "VERIFICATO": "#10b981",
                "PARZIALMENTE_VERO": "#f59e0b",
                "DUBBIO": "#f97316",
                "DISINFORMAZIONE": "#ef4444",
                "INCERTO": "#6b7280"
            }
            colore = colore_map.get(label, "#6b7280")

            # Mappa verdetto label in italiano
            label_map = {
                "VERIFICATO": "Informazione verificata",
                "PARZIALMENTE_VERO": "Parzialmente vero",
                "DUBBIO": "Informazione dubbia",
                "DISINFORMAZIONE": "Disinformazione",
                "INCERTO": "Non verificabile"
            }
            verdetto_testo = label_map.get(label, label)

            # Costruisci fonti reali per il frontend
            fonti_frontend = []
            for v in verdetti:
                top_sources = v["verdetto"].get("top_sources", {})
                for src in top_sources.get("supporting", []):
                    fonti_frontend.append({
                        "nome": src.get("title", "Fonte"),
                        "snippet": src.get("reason", ""),
                        "url": src.get("url", "")
                    })
                for src in top_sources.get("conflicting", []):
                    fonti_frontend.append({
                        "nome": src.get("title", "Fonte"),
                        "snippet": src.get("reason", ""),
                        "url": src.get("url", "")
                    })

            # Se non ci sono fonti dal verdetto, usa quelle dalla pipeline
            if not fonti_frontend:
                for v in verdetti:
                    for src in v.get("fonti_reali", [])[:2]:
                        fonti_frontend.append({
                            "nome": src.get("metadata", {}).get("site_name", "") or src.get("metadata", {}).get("title", "Fonte"),
                            "snippet": src.get("metadata", {}).get("description", "")[:150] if src.get("metadata", {}).get("description") else src.get("article_text", "")[:150],
                            "url": src.get("url", "")
                        })

            risultato_frontend = {
                "affidabilita": truth_pct,
                "verdetto": verdetto_testo,
                "colore": colore,
                "fonti": fonti_frontend[:4],  # Max 4 fonti
                "dettagli": {
                    "explainability": main.get("explainability", {}),
                    "analysis_tags": main.get("analysis_tags", []),
                    "claims_analizzati": len(verdetti)
                }
            }
        else:
            risultato_frontend = {
                "affidabilita": 0,
                "verdetto": "Errore nell'analisi",
                "colore": "#6b7280",
                "fonti": []
            }

        print(f"✅ Analisi completata: {risultato_frontend['verdetto']} ({risultato_frontend['affidabilita']}%)")
        return jsonify(risultato_frontend)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Errore pipeline: {e}")
        return jsonify({"error": f"Errore durante l'analisi: {str(e)}"}), 500

# --- AVVIO DEL SERVER (SOSTITUISCI IL FINALE) ---
if __name__ == '__main__':
    # Usiamo 127.0.0.1 invece di 0.0.0.0 per essere "amici" di Safari
    print("🚀 Truth Shield Server attivo su http://127.0.0.1:5001")
    app.run(host='127.0.0.1', port=5001, debug=True)