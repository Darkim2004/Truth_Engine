import json

def genera_verdetto_probabilistico(claim, dossier_arricchito):
    """
    Esecutore Matematico: Riceve il dossier con i chunk già classificati dal LLM (Confuta/Conferma)
    e applica LA MATEMATICA.
    """
    punti_conferma = 0.0
    punti_confuta = 0.0
    
    fonti_supporto = []
    fonti_smentita = []

    for fonte in dossier_arricchito:
        score_fonte = fonte.get("score_fonte", 1.0)
        url = fonte.get("url", "")
        domain = url.split("//")[-1].split("/")[0] if url else "Sconosciuto"
        
        for chunk in fonte.get("chunks_analizzati", []):
            cat = chunk.get("categoria", "NON_ATTINENTE")
            motivo = chunk.get("motivazione", "")
            
            if cat == "CONFERMA":
                punti_conferma += score_fonte
                fonti_supporto.append({
                    "url": url, 
                    "reason": f"[Peso {score_fonte}] {motivo}", 
                    "title": domain
                })
            elif cat == "CONFUTA":
                punti_confuta += score_fonte
                fonti_smentita.append({
                    "url": url, 
                    "reason": f"[Peso {score_fonte}] {motivo}", 
                    "title": domain
                })
                
    totale_punti = punti_conferma + punti_confuta
    
    if totale_punti == 0:
        verdict_label = "INCERTO"
        perc_truth = 0
        perc_falsity = 0
        perc_uncert = 100
    else:
        perc_truth = int(round((punti_conferma / totale_punti) * 100))
        perc_falsity = int(round((punti_confuta / totale_punti) * 100))
        # Ajust perc to sum to 100 just in case of rounding errors
        if perc_truth + perc_falsity != 100:
            if perc_truth > perc_falsity:
                perc_truth = 100 - perc_falsity
            else:
                perc_falsity = 100 - perc_truth
                
        perc_uncert = 0
        
        if punti_conferma > punti_confuta:
            verdict_label = "VERIFICATO"
        elif punti_confuta > punti_conferma:
            verdict_label = "DISINFORMAZIONE"
        else:
            verdict_label = "INCERTO"
            perc_truth = 50
            perc_falsity = 50
            
    summary = f"Verdetto matematico: {punti_conferma} punti per la conferma e {punti_confuta} punti per la smentita."
   
    return {
        "percentages": { 
            "truth": perc_truth, 
            "falsity": perc_falsity, 
            "uncertainty": perc_uncert
        },
        "verdict_label": verdict_label,
        "explainability": {
            "summary": summary,
            "cross_check_result": f"Punteggi -> Conferma: {punti_conferma} | Confuta: {punti_confuta}",
            "strength_analysis": "Il calcolo si basa sulla somma del peso (affidabilità) della fonte moltiplicato per ogni evidenza testuale (chunk) trovata e classificata.",
            "consensus_level": "Alto" if max(perc_truth, perc_falsity) > 70 else ("Basso" if totale_punti > 0 else "Nessuno"),
            "next_step": "Nessun ulteriore approfondimento." if max(perc_truth, perc_falsity) > 80 else "Raccogliere ulteriori fonti."
        },
        "top_sources": {
            "supporting": fonti_supporto[:5], # Limitiamo per la UI
            "conflicting": fonti_smentita[:5]
        },
        "analysis_tags": ["Calcolo Matematico", verdict_label]
    }