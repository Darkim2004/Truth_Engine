from urllib.parse import urlparse

def extract_domain(url):
    """
    Trasforma 'https://www.ansa.it/news/123' in 'ansa.it'
    """
    try:
        # Prende l'indirizzo base (netloc)
        domain = urlparse(url).netloc
        # Rimuove il 'www.' se presente
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return url # Ritorna l'originale se l'URL è malformato

def get_credibility_score(domain):
    """
    Questa è la tua funzione 'base_domain_score'. 
    Controlla se il dominio è in Whitelist o Blacklist.
    """
    whitelist = {
        "ansa.it": 0.95, "reuters.com": 0.95, "apnews.com": 0.95,
        "istat.it": 1.0, "governo.it": 1.0, "who.int": 1.0,
        "ilsole24ore.com": 0.9, "corriere.it": 0.85, "bbc.co.uk": 0.85
    }
    blacklist = ["bufale.net", "stopcensura.online"]
    
    # 1. Pulizia extra (se per caso è passato un URL intero invece del solo dominio)
    clean_domain = extract_domain(domain) if "/" in domain else domain

    # 2. Controllo logico
    if any(b in clean_domain for b in blacklist):
        return 0.15
    for trusted, score in whitelist.items():
        if trusted in clean_domain:
            return score
    if clean_domain.endswith((".gov", ".edu", ".int")):
        return 0.9
        
    return 0.5 # Default Neutro

def get_source_credibility(url, text):
    domain = extract_domain(url) # Funzione per pulire l'URL
    
    # 1. Base Score dal Dominio (quello che abbiamo già fatto)
    base_score = get_base_domain_score(domain) 
    
    # 2. Correttori Dinamici basati sul Testo
    penalty = 0
    bonus = 0
    
    # Esempio: Il testo cita fonti o dati numerici?
    if any(char.isdigit() for char in text) and ("%" in text or "dati" in text.lower()):
        bonus += 0.05
        
    # Esempio: Il testo usa linguaggio troppo emotivo? (Red Flag)
    emotive_words = ["incredibile", "scandalo", "assurdo", "non crederai"]
    if any(word in text.lower() for word in emotive_words):
        penalty += 0.2
        
    final_score = max(0.1, min(1.0, base_score + bonus - penalty))
    return final_score