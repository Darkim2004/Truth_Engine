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
    Calcola il punteggio di credibilità di base per un dominio.
    Applica regole specifiche invece di whitelist/blacklist statiche.
    """
    # 1. Pulizia extra (se per caso è passato un URL intero invece del solo dominio)
    clean_domain = extract_domain(domain) if "/" in domain else domain
    clean_domain = clean_domain.lower()

    if clean_domain.endswith(".gov"):
        return 1.0

    if "blog" in clean_domain:
        return 0.2

    quotidiani_maggiori = [
        "corriere.it", "repubblica.it", "ilsole24ore.com", "lastampa.it",
        "ilgiornale.it", "liberoquotidiano.it", "ansa.it",
        "nytimes.com", "bbc.co.uk", "reuters.com", "theguardian.com",
        "wikipedia.org"
    ]
    if any(q in clean_domain for q in quotidiani_maggiori):
        return 0.8

    return 0.5 # Default Neutro

def get_source_credibility(url, text):
    domain = extract_domain(url) # Funzione per pulire l'URL
    
    # 1. Base Score dal Dominio (quello che abbiamo già fatto)
    base_score = get_credibility_score(domain) 
    
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