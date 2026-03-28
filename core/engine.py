import json
import os
from core.tabella_pesi import get_credibility_score, extract_domain
from core.classificatore_evidenze import analyze_context_match
from core.motore_verdetto import genera_verdetto_probabilistico

def salva_per_matteo(risultato, nome_file="output_per_ui.json"):
    """Salva il verdetto finale in un JSON leggibile dal Frontend."""
    with open(nome_file, 'w', encoding='utf-8') as f:
        json.dump(risultato, f, indent=4, ensure_ascii=False)
    print(f"\n✅ FILE GENERATO PER MATTEO: {nome_file}")

def genera_dossier_completo(claim, search_results):
    """
    FASE 3: Analizza ogni singola fonte fornita da Andrea.
    Riceve: [{'url': ..., 'text': ..., 'metadata': {...}}, ...]
    """
    evidenze_validate = []

    for res in search_results:
        # 1. Pulizia dominio e punteggio autorità (da tabella_pesi.py)
        domain = extract_domain(res['url'])
        score_fonte = get_credibility_score(domain)
        
        # 2. Analisi semantica con Groq (da classificatore_evidenze.py)
        # Capisce se il testo conferma o smentisce il claim
        analisi_ia = analyze_context_match(res['text'], claim)
        
        # 3. Impacchettamento dei dati per il Giudice Supremo
        info = {
            "url": res['url'],
            "text": res['text'],
            "metadata": res.get('metadata', {}), # Dati extra di Andrea (date, autori)
            "score_fonte": score_fonte,
            "classificazione": analisi_ia['categoria'], 
            "rilevanza": analisi_ia['rilevanza'],
            "motivazione": analisi_ia['motivazione']
        }
        
        evidenze_validate.append(info)

    return evidenze_validate

def truth_engine_main(claim, search_results):
    """
    FUNZIONE MASTER (Quella che deve chiamare Andrea)
    Coordina il passaggio dalla Fase 3 alla Fase 4.
    """
    print(f"\n🚀 TRUTH ENGINE AVVIATO")
    print(f"🔎 Claim: {claim}")
    print(f"📚 Analisi di {len(search_results)} fonti in corso...")

    # STEP 1: Validazione analitica di ogni fonte (Dossier)
    dossier = genera_dossier_completo(claim, search_results)
    
    # STEP 2: Verdetto Probabilistico e Explainability (Giudice Supremo)
    # Questa funzione usa Groq per pesare tutto il dossier insieme
    print("🧠 Il Giudice Supremo sta elaborando il verdetto finale...")
    verdetto_finale = genera_verdetto_probabilistico(claim, dossier)
    
    # STEP 3: Export per il Frontend di Matteo
    salva_per_matteo(verdetto_finale)
    
    print("🏁 Elaborazione completata con successo.\n")
    return verdetto_finale

# --- ESEMPIO DI UTILIZZO PER DEBUG ---
if __name__ == "__main__":
    # Questo blocco serve solo per testare engine.py da solo
    test_claim = "L'acqua calda congela più velocemente della fredda"
    test_results = [
        {
            "url": "https://scienza.edu/esperimento",
            "text": "L'effetto Mpemba conferma che in certe condizioni l'acqua calda congela prima.",
            "metadata": {"date": "2025", "author": "Prof. Rossi", "has_citations": True}
        }
    ]
    # truth_engine_main(test_claim, test_results)