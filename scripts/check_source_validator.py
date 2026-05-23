import os

from dotenv import load_dotenv

from core.source_validator import validate_evidence


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        print(f"GROQ_API_KEY loaded: {api_key[:5]}...")
    else:
        print("GROQ_API_KEY is not configured.")

    result = validate_evidence(
        "https://www.ansa.it",
        "Il prezzo del gas è calato secondo i dati ufficiali.",
        "Calo prezzi gas",
    )
    print(result)


if __name__ == "__main__":
    main()
