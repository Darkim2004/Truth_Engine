import json

from core.engine import truth_engine_main


def main() -> None:
    claim = "Le proteine degli insetti modificano il DNA umano"
    search_results = [
        {
            "url": "https://www.nature.com/articles/s41598-026-12345",
            "text": (
                "Comprehensive analysis of insect-based proteins confirms no "
                "genomic integration in human somatic cells. The amino acid "
                "profile is safe for consumption."
            ),
            "metadata": {"author": "Scientific Team", "date": "2026-01-10"},
        },
        {
            "url": "https://verita-nascoste-blog.it/pericolo-insetti",
            "text": (
                "ATTENZIONE! Gli scienziati pagati dalle lobby dicono che "
                "questi alimenti sono sicuri, ma in realtà il loro DNA si "
                "fonde con il nostro cambiando chi siamo."
            ),
            "metadata": {"author": "Admin99", "date": "2025-11-20"},
        },
    ]

    print("Running manual core + scoring integration check...")
    result = truth_engine_main(claim, search_results)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
