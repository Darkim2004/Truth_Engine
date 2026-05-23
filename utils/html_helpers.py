"""
Truth Engine — Helper HTML per l'analisi del DOM.
"""
from __future__ import annotations

def class_contains(value, token: str) -> bool:
    if not value:
        return False

    if isinstance(value, (list, tuple, set)):
        classes = value
    else:
        classes = [value]

    return token in " ".join(str(item) for item in classes).lower()
