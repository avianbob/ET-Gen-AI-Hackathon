"""
Drug Information Quick-Lookup Endpoint

Provides fast drug metadata (class, mechanism, indications, manufacturer)
without running the full 18-agent pipeline. Uses OpenFDA API with local caching.
"""

import logging
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache directory
CACHE_DIR = Path("data/cache/drug_info")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 24

OPENFDA_BASE = "https://api.fda.gov/drug/label.json"


class DrugInfoResponse(BaseModel):
    """Drug information response model."""
    drug_name: str
    generic_name: Optional[str] = None
    brand_names: List[str] = []
    drug_class: Optional[str] = None
    mechanism: Optional[str] = None
    approved_indications: List[str] = []
    manufacturer: Optional[str] = None
    route: Optional[str] = None
    source: str = "openfda"
    cached: bool = False


def _cache_key(drug_name: str) -> str:
    """Generate cache filename."""
    normalized = drug_name.strip().lower()
    hash_val = hashlib.md5(normalized.encode()).hexdigest()[:12]
    return f"{normalized.replace(' ', '_')}_{hash_val}.json"


def _read_cache(drug_name: str) -> Optional[dict]:
    """Read from cache if valid."""
    cache_file = CACHE_DIR / _cache_key(drug_name)
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return data
    except Exception:
        pass
    return None


def _write_cache(drug_name: str, data: dict):
    """Write to cache."""
    cache_file = CACHE_DIR / _cache_key(drug_name)
    try:
        data["_cached_at"] = datetime.now().isoformat()
        cache_file.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.warning(f"Failed to write drug info cache: {e}")


def _truncate(text: Optional[str], max_len: int = 500) -> Optional[str]:
    """Truncate long text fields."""
    if not text:
        return None
    return text[:max_len] + "..." if len(text) > max_len else text


def _extract_indications(text: Optional[str]) -> List[str]:
    """Extract individual indications from a text block."""
    if not text:
        return []
    # Take first 500 chars, split by common delimiters
    snippet = text[:500]
    # Simple extraction: split by periods and take meaningful segments
    sentences = [s.strip() for s in snippet.split(".") if len(s.strip()) > 10]
    return sentences[:5]  # Max 5 indications


@router.get("/drug-info/{drug_name}", response_model=DrugInfoResponse)
async def get_drug_info(drug_name: str):
    """
    Quick drug information lookup.

    Returns drug class, mechanism, approved indications, and manufacturer
    from OpenFDA. Fast (~200ms) with 24-hour caching.
    """
    drug_name = drug_name.strip()
    if not drug_name:
        raise HTTPException(status_code=400, detail="Drug name is required")

    # Check cache first
    cached = _read_cache(drug_name)
    if cached:
        cached.pop("_cached_at", None)
        return DrugInfoResponse(**cached, cached=True)

    # Query OpenFDA
    result = await _fetch_from_openfda(drug_name)

    # Cache the result
    _write_cache(drug_name, result)

    return DrugInfoResponse(**result, cached=False)


async def _fetch_from_openfda(drug_name: str) -> dict:
    """Fetch drug information from OpenFDA API."""
    result = {
        "drug_name": drug_name,
        "generic_name": None,
        "brand_names": [],
        "drug_class": None,
        "mechanism": None,
        "approved_indications": [],
        "manufacturer": None,
        "route": None,
        "source": "openfda",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try brand name search first
            params = {
                "search": f'openfda.brand_name:"{drug_name}"',
                "limit": 1,
            }
            response = await client.get(OPENFDA_BASE, params=params)

            # If brand name fails, try generic name
            if response.status_code != 200:
                params["search"] = f'openfda.generic_name:"{drug_name}"'
                response = await client.get(OPENFDA_BASE, params=params)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if results:
                    label = results[0]
                    openfda = label.get("openfda", {})

                    result["generic_name"] = (
                        openfda.get("generic_name", [None])[0]
                    )
                    result["brand_names"] = openfda.get("brand_name", [])[:5]
                    result["manufacturer"] = (
                        openfda.get("manufacturer_name", [None])[0]
                    )
                    result["route"] = (
                        openfda.get("route", [None])[0]
                    )

                    # Drug class from pharm_class
                    pharm_classes = openfda.get("pharm_class_epc", [])
                    if pharm_classes:
                        result["drug_class"] = pharm_classes[0]
                    else:
                        # Try MoA class
                        moa_classes = openfda.get("pharm_class_moa", [])
                        if moa_classes:
                            result["drug_class"] = moa_classes[0]

                    # Mechanism of action
                    mechanism = label.get("mechanism_of_action", [None])
                    if isinstance(mechanism, list) and mechanism:
                        result["mechanism"] = _truncate(mechanism[0])
                    elif isinstance(mechanism, str):
                        result["mechanism"] = _truncate(mechanism)

                    # Indications
                    indications = label.get("indications_and_usage", [None])
                    if isinstance(indications, list) and indications:
                        result["approved_indications"] = _extract_indications(
                            indications[0]
                        )
                    elif isinstance(indications, str):
                        result["approved_indications"] = _extract_indications(
                            indications
                        )

            else:
                logger.info(
                    f"OpenFDA returned {response.status_code} for {drug_name}"
                )

    except httpx.TimeoutException:
        logger.warning(f"OpenFDA timeout for {drug_name}")
    except Exception as e:
        logger.error(f"OpenFDA error for {drug_name}: {e}")

    return result
