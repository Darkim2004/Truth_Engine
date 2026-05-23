from .engine import genera_dossier_completo
from .classificatore_evidenze import analyze_context_match
from .motore_verdetto import genera_verdetto_probabilistico

classifica_evidenze_batch = analyze_context_match

__all__ = [
    "genera_dossier_completo",
    "analyze_context_match",
    "classifica_evidenze_batch",
    "genera_verdetto_probabilistico",
]
