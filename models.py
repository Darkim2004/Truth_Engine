"""
Truth Engine — Pydantic models per tipizzare il pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# --- Input Models ---

class InputMetadata(BaseModel):
    source_type: str = ""
    timestamp: str = ""
    language: str = ""


class OriginalSource(BaseModel):
    text_content: str = ""
    url: str = ""


class ClaimToVerify(BaseModel):
    id: int
    claim_text: str = ""
    search_query: str = ""
    category: str = ""


class AnalysisSection(BaseModel):
    engine: str = "LLM-Powered"
    claims_to_verify: list[ClaimToVerify] = Field(default_factory=list)


class PipelineInput(BaseModel):
    metadata: InputMetadata = Field(default_factory=InputMetadata)
    original_source: OriginalSource = Field(default_factory=OriginalSource)
    analysis: AnalysisSection = Field(default_factory=AnalysisSection)


# --- Internal Models ---

class SearchResult(BaseModel):
    """Singolo risultato da un motore di ricerca."""
    url: str
    title: str = ""
    snippet: str = ""
    source_engine: str = ""  # "duckduckgo" o "brave"


class FetchedPage(BaseModel):
    """Pagina HTML scaricata."""
    url: str
    html: str = ""
    status_code: int = 0
    fetch_method: str = ""  # "httpx" o "playwright"
    is_valid: bool = False
    error: str = ""


class ArticleMetadata(BaseModel):
    """Metadati estratti con BeautifulSoup."""
    title: str = ""
    author: str = ""
    published_date: str = ""
    description: str = ""
    site_name: str = ""
    canonical_url: str = ""


class ExtractedSource(BaseModel):
    """Contenuto completo estratto da una fonte."""
    url: str
    article_text: str = ""
    metadata: ArticleMetadata = Field(default_factory=ArticleMetadata)
    fetch_method: str = ""
    language_detected: str = ""


class ClaimSources(BaseModel):
    """Un claim con tutte le sue fonti estratte."""
    claim: ClaimToVerify
    sources: list[ExtractedSource] = Field(default_factory=list)


class PipelineOutput(BaseModel):
    """Output finale del pipeline."""
    timestamp: str = ""
    total_claims: int = 0
    total_sources_found: int = 0
    results: list[ClaimSources] = Field(default_factory=list)
