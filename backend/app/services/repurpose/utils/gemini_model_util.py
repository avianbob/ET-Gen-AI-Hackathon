"""
Normalize Gemini model IDs from env (handles deprecated names, quotes, casing).
Kept separate from gemini_client.py to avoid circular imports with config.
"""

from __future__ import annotations

# Google removed these from v1beta generateContent — always remap
_DEPRECATED_SUBSTRINGS = ("gemini-pro", "gemini-1.0-pro", "gemini-1.5-pro")
_DEFAULT = "gemini-2.0-flash"

_EXACT_ALIASES = {
    "gemini-pro": _DEFAULT,
    "models/gemini-pro": _DEFAULT,
    "gemini-1.0-pro": _DEFAULT,
    "gemini-1.5-pro": _DEFAULT,
}


def normalize_gemini_model(model: str | None) -> str:
    raw = (model or "").strip()
    # Strip common .env quoting mistakes
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        raw = raw[1:-1].strip()
    raw = raw.strip()
    if not raw:
        return _DEFAULT

    key_exact = raw.lower()
    if key_exact in _EXACT_ALIASES:
        return _EXACT_ALIASES[key_exact]

    if raw.startswith("models/"):
        tail = raw.split("/", 1)[-1].lower()
        if tail in _EXACT_ALIASES:
            return _EXACT_ALIASES[tail]

    low = raw.lower()
    for bad in _DEPRECATED_SUBSTRINGS:
        if bad in low:
            return _DEFAULT

    return raw
