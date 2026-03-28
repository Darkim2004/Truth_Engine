import json
from core.engine import truth_engine_main

def test_integrazione():
    # 1. IL CLAIM (Quello che scriverebbe l'utente)
    claim_test = "Le proteine dei grilli modificano il DNA umano"

    # 2. I DATI DI ANDREA (Simuliamo quello che Andrea pesca dal web)
    # Ne mettiamo uno "buono" (scientifico) e uno "fuffa" (blog complottista)
    risultati_ricerca = [
        {
            "url": "https://www.nature.com/articles/s41598-026-12345",
            "text": "Comprehensive analysis of insect-based proteins confirms no genomic integration in human somatic cells. The amino acid profile is safe for consumption.",
            "metadata": {"author": "Scientific Team", "date": "2026-01-10", "source_type": "Journal"}
        },
        {
            "url": "https://verita-nascoste-blog.it/pericolo-insetti",
            "text": "ATTENZIONE! Gli scienziati pagati dalle lobby dicono che i grilli sono sicuri, ma in realtà il loro DNA si fonde con il nostro cambiando chi siamo!",
            "metadata": {"author": "Admin99", "date": "2025-11-20", "source_type": "Blog"}
        }
    ]

    print("🚀 AVVIO TEST DI INTEGRAZIONE (CORE + SCORING)...")
    
    try:
        # Chiamiamo la tua funzione Master
        verdetto = truth_engine_main(claim_test, risultati_ricerca)

        # 3. VERIFICA DELL'OUTPUT
        print("\n" + "="*50)
        print("📊 VERDETTO GENERATO CON SUCCESSO!")
        print("="*50)
        
        # Stampiamo i punti chiave per vedere se Groq ha ragionato bene
        print(f"LABEL: {verdetto.get('verdict_label')}")
        print(f"TRUTH %: {verdetto.get('percentages', {}).get('truth')}%")
        print(f"FALSITY %: {verdetto.get('percentages', {}).get('falsity')}%")
        
        print("\n🔗 TOP SOURCES SELEZIONATE:")
        for source in verdetto.get('top_sources', {}).get('supporting', []):
            print(f"✅ PRO: {source['url']} (Motivo: {source['reason']})")
        for source in verdetto.get('top_sources', {}).get('conflicting', []):
            print(f"❌ CONTRO: {source['url']} (Motivo: {source['reason']})")
            
        print("\n🧠 CROSS-CHECK RESULT:")
        print(verdetto.get('explainability', {}).get('cross_check_result'))

    except Exception as e:
        print(f"\n❌ IL TEST È FALLITO!")
        print(f"Errore tecnico: {e}")
        print("\nControlla se:")
        print("1. Hai attivato il .venv")
        print("2. La GROQ_API_KEY nel file .env è corretta")
        print("3. I file evidence_matcher.py e engine.py sono nelle cartelle giuste")

if __name__ == "__main__":
    test_integrazione()