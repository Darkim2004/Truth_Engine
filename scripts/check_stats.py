import json
from pathlib import Path

RESULTS_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "legacy" / "results.json"


def main() -> None:
    with RESULTS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for claim in data["results"]:
        print(f"Claim: {claim['claim']['id']}")
        for source in claim["sources"]:
            print(f"  URL: {source['url']}")
            print(f"  Method: {source['fetch_method']}")
            print(f"  Lang: {source['language_detected']}")
            print(f"  Text Len: {len(source['article_text'])}")
            print("")


if __name__ == "__main__":
    main()
