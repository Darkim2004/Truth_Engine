# Truth Shield

Truth Shield is a Python fact-checking pipeline that extracts verifiable claims from text, searches public sources, scores evidence relevance, and returns a verdict with confidence and explainability data.

It includes:
- A Flask backend API
- A static web dashboard in `front-end/`
- A CLI entry point for JSON-based runs

## Features

- Claim extraction from input text using Groq LLM
- Multi-source search (DuckDuckGo)
- Page fetching with `httpx` and Playwright fallback for dynamic pages
- Content extraction and metadata parsing
- Semantic evidence matching with sentence embeddings
- Final verdict generation with confidence, tags, and top sources

## Tech Stack

- Python 3.11+
- Flask, Flask-CORS
- Groq API
- `ddgs` (DuckDuckGo search)
- `httpx`, Playwright
- `trafilatura`, BeautifulSoup4
- `sentence-transformers`, scikit-learn, numpy
- Pydantic

## Project Structure

```text
.
|-- app.py                     # Flask app and API endpoints
|-- main.py                    # CLI entry point
|-- pipeline.py                # Main async pipeline orchestration
|-- models.py                  # Pydantic input/output models
|-- config.py                  # Central configuration
|-- core/                      # Verdict engine and credibility logic
|-- search/                    # Search aggregation and providers
|-- fetcher/                   # HTTP and Playwright fetchers
|-- extractor/                 # Text and metadata extraction
|-- scoring/                   # Embeddings and evidence matching
|-- utils/                     # URL/language/paywall utilities
|-- front-end/                 # Static UI assets
`-- test_*.py                  # Integration and backend tests
```

## Prerequisites

- Python 3.11 or newer
- A valid Groq API key (`GROQ_API_KEY`)
- Network access (Groq + web search)

## Quick Start

### One-Command Startup (Windows PowerShell)

Use the startup script to automate setup and launch:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

What the script does:
- asks for `GROQ_API_KEY` at the beginning (if missing in `.env`)
- saves or updates `GROQ_API_KEY` in `.env`
- creates `.venv` if it does not exist
- upgrades `pip`
- installs dependencies from `requirements.txt`
- installs Playwright browser
- starts `app.py`

First run can take a few minutes because package and browser installation is performed automatically.

### 1) Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows (cmd):

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Install Playwright browsers

```bash
python -m playwright install
```

### 4) Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_key_here
```

### 5) Run the web server

```bash
python app.py
```

Default server URL:
- `http://127.0.0.1:5001`

## Usage

### Web Dashboard

Open:
- `http://127.0.0.1:5001`

The backend serves static assets from `front-end/`.

### CLI

Run pipeline with JSON input file:

```bash
python main.py --input input_example.json --output results.json
```

Print output to stdout:

```bash
python main.py --input input_example.json
```

Quick script:

```bash
python run_test.py
```

This reads `input_example.json` and writes `raw_output.json`.

## API Endpoints

### `GET /`
Serves `front-end/index.html`.

### `POST /api/verify`
Direct verdict from a claim and source results.

Example payload:

```json
{
  "claim": "Sample claim",
  "results": [
    {
      "url": "https://example.com",
      "text": "Article text",
      "metadata": { "title": "Example" }
    }
  ]
}
```

### `POST /elabora`
Preprocessing endpoint used by the UI.

Example payload:

```json
{
  "mode": "testo",
  "data": "Text to analyze"
}
```

or

```json
{
  "mode": "url",
  "data": "https://example.com/news"
}
```

### `POST /elabora_completo`
Full flow:
1. Claim extraction with Groq
2. Search and fetch pipeline
3. Evidence scoring
4. Final verdict mapping for frontend

Example payload:

```json
{
  "mode": "testo",
  "data": "Text to fact-check"
}
```

## Input and Output Models

Main schema definitions are in `models.py`.

Input root model: `PipelineInput`
- `metadata`
- `original_source`
- `analysis.claims_to_verify[]`

Output root model: `PipelineOutput`
- `timestamp`
- `total_claims`
- `total_sources_found`
- `results[]` with per-claim sources and scoring data

Sample files:
- `input_example.json`
- `results.json`
- `output_per_ui.json`

## Testing

Run all `unittest` tests:

```bash
python -m unittest discover -v
```

Run specific tests:

```bash
python -m unittest test_backend_end_to_end.py -v
python -m unittest test_backend_live_external.py -v
python -m unittest core.test_fase4 -v
```

Notes:
- `test_backend_live_external.py` is optional and skipped unless enabled.
- To enable live test:

```bash
set RUN_LIVE_E2E=1
python -m unittest test_backend_live_external.py -v
```

On PowerShell:

```powershell
$env:RUN_LIVE_E2E="1"
python -m unittest test_backend_live_external.py -v
```

## Configuration

Global defaults are in `config.py`, including:
- Search limits and retry policy
- HTTP timeout and concurrency
- Playwright timeout and scroll behavior
- Chunking and embedding thresholds
- URL tracking parameter cleanup
- Paywall keyword heuristics

Environment variable:
- `GROQ_API_KEY` (required)

## Architecture Summary

High-level flow:
1. User submits text/URL
2. Claims and search queries are generated
3. Search results are aggregated and deduplicated
4. Pages are fetched (`httpx`, fallback Playwright)
5. Text and metadata are extracted
6. Relevant chunks are scored by semantic similarity
7. Core engine builds final verdict and explainability output

Main orchestrator:
- `pipeline.py`

Verdict logic:
- `core/engine.py`
- `core/motore_verdetto.py`
- `core/classificatore_evidenze.py`

## Known Limitations

- Requires external services (Groq API and web search availability)
- Dynamic sites can increase latency due to Playwright fallback
- Language and paywall detection are heuristic-based
- Live tests depend on network and valid credentials

## Contributing

1. Create a branch
2. Keep changes focused
3. Run relevant tests
4. Open a pull request with a clear description

## License

No license file is currently defined in this repository.
Add a `LICENSE` file before public distribution.
