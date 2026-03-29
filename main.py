"""
Truth Engine — Entry point CLI.
Legge JSON input, esegue il pipeline, scrive JSON output.

Uso:
    python main.py --input claims.json --output results.json
    python main.py --input claims.json  (output su stdout)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from rich.console import Console

from pipeline import run_pipeline

console = Console(legacy_windows=False)


def main():
    parser = argparse.ArgumentParser(
        description="Truth Engine — Crawling & Scraping Pipeline",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path al file JSON di input con i claims da verificare.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Path al file JSON di output. Se omesso, stampa su stdout.",
    )

    args = parser.parse_args()

    # Leggi input
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Errore:[/red] File non trovato: {args.input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Errore:[/red] JSON non valido: {e}")
        sys.exit(1)

    # Esegui pipeline
    try:
        output = asyncio.run(run_pipeline(input_data))
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrotto dall'utente.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Errore pipeline:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Scrivi output
    output_json = output.model_dump_json(indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        console.print(f"\n[green]Output salvato in:[/green] {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
