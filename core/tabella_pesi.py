import os
import json
from urllib.parse import urlparse

# Caricamento della libreria fonti massiva (Dataset Fact-Check)
LIBRERIA_FONTI = {}
dataset_path = os.path.join(os.path.dirname(__file__), 'libreria_fonti.json')
if os.path.exists(dataset_path):
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            LIBRERIA_FONTI = json.load(f)
    except Exception as e:
        print(f"[WARNING] Impossibile caricare libreria_fonti.json: {e}")

CATEGORIE_ALTA_AFFIDABILITA = ["reliable"]
CATEGORIE_MEDIA_AFFIDABILITA = ["bias", "satire", "clickbait"]
CATEGORIE_FALSA_AFFIDABILITA = ["fake", "conspiracy", "junksci", "hate", "unreliable"]

def extract_domain(url):
    """
    Trasforma 'https://www.ansa.it/news/123' in 'ansa.it'
    """
    try:
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return url

def get_credibility_score(domain):
    """
    Calcola il punteggio interpolando la libreria internazionale e la whitelist italiana.
    """
    clean_domain = extract_domain(domain) if "/" in domain else domain
    clean_domain = clean_domain.lower()

    # 1. Eccezioni Massima Autorità (Istituzioni e Wikipedia)
    if clean_domain.endswith(".gov") or "wikipedia." in clean_domain:
        return 1.0

    # 2. Controllo contro la Libreria OpenSources (800+ domini catalogati)
    if clean_domain in LIBRERIA_FONTI:
        tipo = str(LIBRERIA_FONTI[clean_domain].get("type", "")).lower()
        if tipo in CATEGORIE_ALTA_AFFIDABILITA:
            return 0.9
        elif tipo in CATEGORIE_MEDIA_AFFIDABILITA:
            return 0.3
        elif tipo in CATEGORIE_FALSA_AFFIDABILITA:
            return 0.1

    # 3. Whitelist Quotidiani Italiani/Esterni Maggiori (Fallback)
    quotidiani_maggiori = [
        "corriere.it", "repubblica.it", "ilsole24ore.com", "lastampa.it",
        "ilgiornale.it", "liberoquotidiano.it", "ansa.it",
        "nytimes.com", "bbc.co.uk", "reuters.com", "theguardian.com"
    ]
    if any(q in clean_domain for q in quotidiani_maggiori):
        return 0.8

    # 4. Regole Euristiche Generiche
    if "blog" in clean_domain:
        return 0.2

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