# Truth Shield

Truth Shield is a Python fact-checking pipeline built during a 48-hour hackathon. It extracts verifiable claims from text or URLs, searches public sources, scores evidence relevance, and returns a verdict with confidence and explainability data.

The project includes a Flask backend API, a static dashboard, and a CLI for JSON-based pipeline runs.

## Features

- Claim extraction from free text or article metadata with Groq
- Multi-source web search with DuckDuckGo
- Page fetching with `httpx` and a Playwright fallback for dynamic pages
- Article text and metadata extraction
- Semantic evidence matching with sentence embeddings
- Weighted verdict generation using source credibility and evidence classification
- Frontend-ready JSON output for confidence, verdict labels, source cards, and details

## Tech Stack

- Python 3.11, 3.12, or 3.13
- Flask and Flask-CORS
- Groq API
- `ddgs` for DuckDuckGo search
- `httpx`, Playwright, `playwright-stealth`
- `trafilatura`, BeautifulSoup4
- `sentence-transformers`, scikit-learn, numpy
- Pydantic

## Project Structure

```text
.
|-- app.py                  # Flask app and API endpoints
|-- main.py                 # CLI entry point
|-- start.py                # Setup/start helper
|-- config.py               # Central configuration and runtime paths
|-- core/                   # Pipeline, models, verdict engine, source credibility logic
|-- search/                 # Search aggregation and providers
|-- fetcher/                # HTTP and Playwright fetchers
|-- extractor/              # Text and metadata extraction
|-- scoring/                # Embeddings, chunking, evidence matching
|-- utils/                  # URL, language, and paywall utilities
|-- front-end/              # Static dashboard assets
|-- tests/                  # Automated unit and integration tests
|-- scripts/                # Example/manual helper scripts
`-- examples/               # Example input payloads
```

Runtime files, debug logs, and legacy run artifacts are written outside the source tree and ignored by Git.

## Quick Start

### One-command setup

```bash
python start.py
```

The startup script asks for `GROQ_API_KEY` if needed, creates `.venv`, installs dependencies, checks Playwright Chromium, and starts the Flask app.

### Manual setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Create `.env` from `.env.example`:

```env
GROQ_API_KEY=gsk_your_key_here
```

Run the server:

```bash
python app.py
```

Open `http://127.0.0.1:5001`.

### Docker

Docker Desktop, or another Docker daemon, must be running before executing these
commands. On Windows, if Docker reports that it cannot connect to
`//./pipe/docker_engine`, start Docker Desktop and retry.

Build the image:

```bash
docker build -t truth-shield .
```

The first build can take a while because Playwright installs Chromium and the
required system dependencies inside the image.

Run the Flask API and static dashboard:

```bash
docker run --rm -p 5001:5001 --env-file .env truth-shield
```

Open `http://127.0.0.1:5001`.

## CLI Usage

Run the pipeline with the example input:

```bash
python main.py --input examples/input_example.json --output .runtime/outputs/results.json
```

Print output to stdout:

```bash
python main.py --input examples/input_example.json
```

Run the helper script:

```bash
python scripts/example_pipeline.py
```

## API Endpoints

### `GET /`

Serves the static dashboard from `front-end/index.html`.

### `POST /elabora_completo`

Runs the full flow: claim extraction, search, fetch, scoring, verdict, and frontend mapping.

```json
{ "mode": "testo", "data": "Text to fact-check" }
```

## Testing

Run the automated suite:

```bash
python -m unittest discover -s tests -v
```

Run specific tests:

```bash
python -m unittest tests.test_backend_end_to_end -v
python -m unittest tests.test_evidence_scoring -v
```

The live external test is skipped by default. To enable it:

```powershell
$env:RUN_LIVE_E2E="1"
python -m unittest tests.test_backend_live_external -v
```

It requires network access and a valid `GROQ_API_KEY`.

## Architecture Summary

1. The user submits text or a URL.
2. Groq extracts up to three verifiable claims and search queries.
3. DuckDuckGo returns candidate sources.
4. URLs are normalized and deduplicated.
5. Pages are fetched with `httpx`, falling back to Playwright when needed.
6. Content and metadata are extracted.
7. Semantic chunk matching finds relevant evidence.
8. The core engine weights evidence by source credibility and returns a verdict.

Main orchestrator: `core/pipeline.py`

Verdict logic: `core/engine.py`, `core/motore_verdetto.py`, `core/classificatore_evidenze.py`

## Known Limitations

- Requires Groq API access and network availability for full runs.
- First semantic scoring run may download the configured embedding model.
- Paywall and language detection are heuristic-based.
- Dynamic pages are slower because they require the Playwright fallback.

## License

MIT. See `LICENSE`.
