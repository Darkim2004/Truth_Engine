"""
Backward-compatible source validation helpers.

The project now keeps semantic evidence matching in scoring.evidence_matcher.
This module enriches that result with source credibility so old scripts can
keep importing core.source_validator.validate_evidence without duplicating the
scoring logic.
"""
from __future__ import annotations

from core.tabella_pesi import extract_domain, get_credibility_score
from scoring.evidence_matcher import validate_evidence as validate_semantic_evidence


def validate_source_evidence(url: str, text: str, claim: str) -> dict:
    """Return source credibility plus semantic relevance for a claim."""
    domain = extract_domain(url)
    source_score = get_credibility_score(domain)
    semantic = validate_semantic_evidence(url=url, text=text, claim=claim)
    relevance = max(0.0, min(1.0, float(semantic.get("max_similarity", 0.0))))
    final_credibility = (source_score * 0.6) + (relevance * 0.4)

    return {
        "url": url,
        "domain": domain,
        "source_score": source_score,
        "semantic_relevance": relevance,
        "final_credibility": round(final_credibility, 2),
        "category": "ATTINENTE" if semantic.get("supports_claim") else "NON_ATTINENTE",
        "motivazione": (
            "La fonte contiene passaggi semanticamente vicini al claim."
            if semantic.get("supports_claim")
            else "La fonte non contiene passaggi abbastanza vicini al claim."
        ),
        "semantic_analysis": semantic,
    }


def validate_evidence(url: str, text: str, claim: str) -> dict:
    """Compatibility alias used by older manual scripts."""
    return validate_source_evidence(url, text, claim)
