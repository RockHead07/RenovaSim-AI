# ---------------------------------------------------------------------------
# llm_extractor.py
# Communicates with Ollama (llama3.2) to extract structured data from
# free-text Indonesian renovation descriptions.
# Never crashes — always falls back to None on failure.
# ---------------------------------------------------------------------------

import json
import logging
import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
MAX_RETRIES = 2
TIMEOUT = 30.0

EXTRACTION_PROMPT = """You are an information extraction system for Indonesian renovation projects.
Extract structured data from the user's input.
Return ONLY valid JSON. No explanation. No markdown. No code blocks.

Schema:
{{
  "job_type": "painting" | "ceramic" | "electrical" | "plumbing" | "roofing" | "waterproofing" | null,
  "area_m2": number | null,
  "quality": "ekonomi" | "standar" | "premium" | null,
  "location": string | null,
  "scope": "light" | "medium" | "full" | null,
  "room": "bathroom" | "kitchen" | "bedroom" | "living_room" | "roof" | null
}}

Rules:
- Convert dimensions like "3x4", "3x4m", "3 x 4" into area number (e.g. 12)
- Convert "sekitar 20", "kurang lebih 20" to 20
- If unknown or unclear, return null for that field
- Do NOT guess values — only extract what is explicitly stated
- Normalize Indonesian keywords:
  - "cat", "ngecat", "pengecatan" → "painting"
  - "keramik", "kramik", "granit", "lantai" → "ceramic"
  - "listrik", "elektrikal" → "electrical"
  - "pipa", "plumbing", "sanitasi" → "plumbing"
  - "atap", "genteng" → "roofing"
  - "waterproof", "anti bocor" → "waterproofing"
  - "kamar mandi", "toilet", "wc" → room: "bathroom"
  - "dapur" → room: "kitchen"
  - "kamar tidur", "kamar" → room: "bedroom"
  - "ruang tamu", "ruang keluarga" → room: "living_room"
  - "ekonomi", "murah", "biasa" → "ekonomi"
  - "standar", "normal" → "standar"
  - "premium", "bagus", "mewah", "mahal", "impor" → "premium"
  - "ringan", "touch up", "minor" → scope: "light"
  - "total", "bongkar", "full" → scope: "full"

User input: "{text}"

Return only the JSON object:"""


def _parse_llm_response(raw: str) -> dict | None:
    """Parse and validate JSON from LLM response."""
    raw = raw.strip()

    # Strip markdown code blocks if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw

    try:
        data = json.loads(raw)
        # Validate it's a dict with expected keys
        expected_keys = {"job_type", "area_m2", "quality", "location", "scope", "room"}
        if isinstance(data, dict) and any(k in data for k in expected_keys):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to find JSON object in the response
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def extract_from_text(text: str) -> dict | None:
    """
    Send text to Ollama and extract structured renovation data.

    Returns dict with extracted fields, or None if extraction fails.
    Never raises exceptions — all failures return None.
    """
    prompt = EXTRACTION_PROMPT.format(text=text)

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            logger.debug(f"LLM extraction attempt {attempt} for: '{text[:50]}...'")

            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,   # low temp for consistent extraction
                            "top_p": 0.9,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()
                raw_text = data.get("response", "")

            parsed = _parse_llm_response(raw_text)
            if parsed:
                logger.info(f"LLM extraction success on attempt {attempt}: {parsed}")
                return parsed
            else:
                logger.warning(f"LLM attempt {attempt} returned unparseable response: {raw_text[:100]}")

        except httpx.ConnectError:
            logger.warning("Ollama not reachable — falling back to rule-based parser")
            return None
        except httpx.TimeoutException:
            logger.warning(f"LLM attempt {attempt} timed out")
        except Exception as e:
            logger.warning(f"LLM attempt {attempt} failed: {e}")

    logger.warning("All LLM attempts failed — falling back to rule-based parser")
    return None


def merge_llm_with_parsed(llm_result: dict | None, parsed_fields: dict) -> dict:
    """
    Merge LLM extraction with rule-based parsed fields.
    Explicit parsed fields take priority over LLM extraction.
    LLM fills in what rule-based missed.
    """
    if not llm_result:
        return parsed_fields

    merged = dict(llm_result)

    # Explicit fields always win over LLM
    for key, value in parsed_fields.items():
        if value is not None:
            merged[key] = value

    logger.debug(f"Merged result: {merged}")
    return merged