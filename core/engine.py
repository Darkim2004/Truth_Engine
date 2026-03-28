import json
import sys
import os

# Permette a Python di vedere la root del progetto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tabella_pesi import get_credibility_score, extract_domain
from core.motore_verdetto import genera_verdetto_probabilistico
from scoring.evidence_matcher import validate_evidence 

def salva_per_matteo(risultato, nome_file="output_per_ui.json"):
    """Salva il verdetto finale in un JSON leggibile dal Frontend."""
    with open(nome_file, 'w', encoding='utf-8') as f:
        json.dump(risultato, f, indent=4, ensure_ascii=False)
    print(f"\n[OK] FILE GENERATO PER MATTEO: {nome_file}")

def genera_dossier_completo(claim, search_results):
    """
    FASE 3: Riceve i risultati grezzi, chiama lo Scoring di Andrea,
    e aggiunge i Pesi Autorità del Core.
    """
    evidenze_validate = []

    for res in search_results:
        # 1. CHIAMATA AL MOTORE DI ANDREA
        # Gli passiamo url, testo e claim. Lui ci ridà i chunk (matches) e la similarità.
        analisi_andrea = validate_evidence(
            url=res.get('url', ''),
            text=res.get('text', ''),
            claim=claim
        )
        
        # 2. CALCOLO AUTORITÀ (Tuo Core)
        # Estraiamo il dominio e cerchiamo il punteggio nella tua tabella pesi.
        domain = extract_domain(res.get('url', ''))
        score_fonte = get_credibility_score(domain)
        
        # 3. IMPACCHETTAMENTO PER GROQ
        # Costruiamo il dizionario con i dati di Andrea + i tuoi.
        info = {
            "url": res.get('url'),
            "score_fonte": score_fonte, # Tuo peso autorità
            "max_similarity": analisi_andrea.get('max_similarity', 0.0), # Matematica Andrea
            "supports_claim_math": analisi_andrea.get('supports_claim', False), # Soglia Andrea
            # Mandiamo a Groq solo i paragrafi rilevanti (matches) trovati da Andrea
            "top_matches": [m['chunk_text'] for m in analisi_andrea.get('matches', [])],
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
    
    # STEP 2: Il Giudice Supremo (Groq) emette il verdetto
    print("[LLM] Il Giudice Supremo sta elaborando il verdetto finale...")
    verdetto_finale = genera_verdetto_probabilistico(claim, dossier)
    
    # STEP 3: Salvataggio fisico per sicurezza e ritorno per Flask
    salva_per_matteo(verdetto_finale)
    
    print("[FINE] Elaborazione completata con successo.\n")
    return verdetto_finale

if __name__ == "__main__":
    print("[INIT] Engine configurato per ricevere i dati di Andrea e rispondere a Matteo.")