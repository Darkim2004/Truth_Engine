from core.tabella_pesi import get_credibility_score
# Importiamo la funzione corretta dal file corretto
from core.classificatore_evidenze import analyze_context_match 

def genera_dossier_completo(claim, search_results):
    dossier = {
        "claim": claim,
        "evidenze": [],
        "analisi_aggregata": {
            "punteggio_medio_credibilita": 0,
            "presenza_smentite_forti": False
        }
    }

    for res in search_results:
        # Estrazione dominio (La facciamo al volo qui per sicurezza)
        domain = res['url'].split("//")[-1].split("/")[0].replace("www.", "")
        
        # 1. Credibilità dal tuo file tabella_pesi.py
        c_score = get_credibility_score(domain)
        
        # 2. Analisi semantica (Usiamo il nome corretto della funzione)
        analisi = analyze_context_match(res['text'], claim)
        
        # 3. Costruisci il pezzo del dossier con le chiavi che sputa l'LLM
        info = {
            "url": res['url'],
            "score_fonte": c_score,
            "classificazione": analisi['categoria'], 
            "rilevanza": analisi['rilevanza'],
            "motivazione": analisi['motivazione']
        }
        
        dossier["evidenze"].append(info)

    # Calcolo rapido della media per il dossier
    if dossier["evidenze"]:
        media = sum(e['score_fonte'] for e in dossier["evidenze"]) / len(dossier["evidenze"])
        dossier["analisi_aggregata"]["punteggio_medio_credibilita"] = round(media, 2)

    return dossier