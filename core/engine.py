import json
import sys
import os

# Permette a Python di vedere la root del progetto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tabella_pesi import get_credibility_score, extract_domain
from core.motore_verdetto import genera_verdetto_probabilistico
from core.classificatore_evidenze import analyze_context_match
from scoring.evidence_matcher import validate_evidence 

def calcola_affidabilita_media(dossier):
    """
    CALCOLO MATEMATICO: 
    Determina l'affidabilità basandosi solo sull'Autorità delle fonti trovate.
    """
    if not dossier:
        return 0
    
    # Sommiamo i pesi autorità (che vanno da 0.1 a 1.0)
    punteggio_ottenuto = sum([ev.get('score_fonte', 1.0) for ev in dossier])
    # Il massimo teorico è il numero di fonti (se tutte avessero peso 1.0)
    massimo_teorico = len(dossier) * 1.0 
    
    if massimo_teorico == 0: return 0
    # Trasforma in base 100 per la UI del frontend
    return int(round((punteggio_ottenuto / massimo_teorico) * 100))

def salva_per_matteo(risultato, nome_file="output_per_ui.json"):
    """Salva il verdetto finale in un JSON leggibile dal Frontend."""
    with open(nome_file, 'w', encoding='utf-8') as f:
        json.dump(risultato, f, indent=4, ensure_ascii=False)
    print(f"\n[OK] FILE GENERATO PER MATTEO: {nome_file}")

def genera_dossier_completo(claim, search_results):
    """
    FASE 3: Riceve i risultati grezzi, chiama lo Scoring di Andrea,
    estrae i chunk e li classifica singolarmente tramite LLM
    e aggiunge i Pesi Autorità del Core.
    """
    evidenze_validate = []

    for res in search_results:
        # Chiamata al motore di Andrea
        analisi_andrea = validate_evidence(
            url=res.get('url', ''),
            text=res.get('text', ''),
            claim=claim
        )
        
        domain = extract_domain(res.get('url', ''))
        score_fonte = get_credibility_score(domain)
        
        # Estraiamo tutti i chunk testuali trovati da Andrea
        chunks_text_list = [match.get('chunk_text', '') for match in analisi_andrea.get('matches', []) if match.get('chunk_text', '')]
        
        # Analizziamo tutti i chunk in batch con l'LLM (velocissimo, 1 singola chiamata API)
        risultati_llm_batch = analyze_context_match(chunks_text_list, claim) if chunks_text_list else []
        
        chunks_analizzati = []
        for i, chunk_text in enumerate(chunks_text_list):
            risultato = risultati_llm_batch[i] if i < len(risultati_llm_batch) else {"categoria": "NON_ATTINENTE", "motivazione": "Non analizzato"}
            chunks_analizzati.append({
                "testo": chunk_text,
                "categoria": risultato.get("categoria", "NON_ATTINENTE"),
                "motivazione": risultato.get("motivazione", "")
            })
        
        info = {
            "url": res.get('url'),
            "score_fonte": score_fonte,
            "max_similarity": analisi_andrea.get('max_similarity', 0.0),
            "supports_claim_math": analisi_andrea.get('supports_claim', False),
            "top_matches": [m['chunk_text'] for m in analisi_andrea.get('matches', [])],
            "chunks_analizzati": chunks_analizzati,
            "metadata": res.get('metadata', {})
        }
        
        evidenze_validate.append(info)

    return evidenze_validate

def truth_engine_main(claim, search_results):
    """
    FUNZIONE MASTER: Quella che viene chiamata da app.py (Flask).
    """
    print(f"\n[START] TRUTH ENGINE AVVIATO")
    print(f"[RICERCA] Claim: {claim}")
    print(f"[FONTI] Analisi di {len(search_results)} fonti tramite Scoring di Andrea...")

    # STEP 1: Creazione del Dossier Arricchito (Scoring + Pesi)
    dossier = genera_dossier_completo(claim, search_results)
    
    # STEP 2: Calcolo Affidabilità (Media Pesata Autorità)
    score_affidabilita = calcola_affidabilita_media(dossier)
    
    # STEP 3: Il Giudice Supremo (Groq) emette il verdetto
    verdetto_finale = genera_verdetto_probabilistico(claim, dossier)
    
    # STEP 4: Inserimento del dato per il tachimetro di Matteo
    verdetto_finale["confidence_score"] = score_affidabilita
    
    salva_per_matteo(verdetto_finale)
    
    print("[FINE] Elaborazione completata con successo.\n")
    return verdetto_finale

if __name__ == "__main__":
    print("[INIT] Engine configurato per ricevere i dati di Andrea e rispondere a Matteo.")