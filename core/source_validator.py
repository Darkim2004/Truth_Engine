# Importi le funzioni che abbiamo appena scritto sopra
from core.tabella_pesi import extract_domain, get_credibility_score
from core.classificatore_evidenze import analyze_context_match

def validate_evidence(url, text, claim):
    # 1. Pulisci l'URL per avere solo il dominio (es. ansa.it)
    domain = extract_domain(url)
    
    # 2. Ottieni lo score del dominio (la tua "base_domain")
    domain_score = get_credibility_score(domain)
    
    # 3. Chiedi all'LLM se il testo c'entra col claim
    analysis = analyze_context_match(text, claim)
    
    # 4. Calcolo pesato (60% fonte, 40% pertinenza testo)
    final_credibility = (domain_score * 0.6) + (analysis['rilevanza'] * 0.4)
    
    return {
        "final_credibility": round(final_credibility, 2),
        "category": analysis['categoria'],
        "motivazione": analysis['motivazione']
    }