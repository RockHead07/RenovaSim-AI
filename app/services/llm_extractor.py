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
OLLAMA_MODEL = "qwen2.5:7b"
MAX_RETRIES = 2
TIMEOUT = 120.0

EXTRACTION_PROMPT = """Anda adalah sistem ekstraksi informasi untuk proyek renovasi di Indonesia.
Ekstrak data terstruktur dari input pengguna.
Kembalikan HANYA JSON yang valid. Tanpa penjelasan. Tanpa markdown. Tanpa blok kode.

Skema:
{{
  "job_types": ["painting", "ceramic"],
  "area_m2": number | null,
  "quality": "ekonomi" | "standar" | "premium" | null,
  "location": string | null,
  "scope": "light" | "medium" | "full" | null,
  "room": "bathroom" | "kitchen" | "bedroom" | "living_room" | "roof" | null
}}

Nilai valid untuk job_types (ARRAY — ekstrak SEMUA pekerjaan yang disebutkan):
- "painting"       → cat dinding, cat plafon, cat ulang, poles, repaint, ngecat, pengecatan, warna
- "ceramic"        → keramik, lantai, ubin, tiles, granit, ganti lantai, pasang lantai
- "plumbing"       → pipa, kran, wastafel, toilet, saluran air, bak mandi, shower
- "electrical"     → listrik, kabel, stopkontak, lampu pasang, instalasi listrik, pasang AC, AC, air conditioner, kipas angin
- "roofing"        → atap, genteng, bocor atap, talang
- "waterproofing"  → waterproof, anti bocor, coating anti air, pelapis
- "carpentry"      → pintu, jendela, kusen, lemari, partisi kayu, ganti pintu, plafon kayu

Aturan PENTING:
- job_types adalah ARRAY. Ekstrak SEMUA pekerjaan yang disebutkan, jangan hanya satu.
- Contoh input: "cat dinding, ganti lantai keramik, pasang AC" → job_types: ["painting", "ceramic", "electrical"]
- Contoh input: "renovasi kamar, cat premium, ganti pintu, lantai keramik, plafon, pasang AC" → job_types: ["painting", "carpentry", "ceramic", "electrical"]
- Cat dinding dan cat plafon keduanya → "painting" (tidak duplikasi dalam array)
- Jika hanya satu pekerjaan → tetap array: ["painting"]
- Jika tidak ada pekerjaan disebutkan → job_types: []
- Jika dimensi seperti '4x5', '4 x 5', '4mx5m' → hitung: area_m2 = 20
- "sekitar 20", "kurang lebih 20" → area_m2 = 20
- Scope: "renovasi total/full/bongkar/semua" → "full", "ringan/touch up/sedikit" → "light", selain itu null
- Quality: "premium/bagus/mewah/mahal/impor" → "premium", "ekonomi/murah/biasa" → "ekonomi", "standar/normal" → "standar"
- Location: kota atau daerah yang disebutkan (jakarta, surabaya, dll), selain itu null

Input pengguna: "{text}"

Kembalikan hanya objek JSON:"""


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
        expected_keys = {"job_types", "job_type", "area_m2", "quality", "location", "scope", "room"}
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
                # Post-process: calculate area from dimensions if area is null
                import re
                if not parsed.get('area_m2'):
                    dim_pattern = r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*m?'
                    match = re.search(dim_pattern, text)
                    if match:
                        w = float(match.group(1))
                        h = float(match.group(2))
                        parsed['area_m2'] = w * h

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

    # Backward compatibility: normalize job_type → job_types
    if "job_types" not in merged or not merged["job_types"]:
        single = merged.get("job_type")
        merged["job_types"] = [single] if single else []

    # Deduplicate job_types
    seen = []
    for jt in merged.get("job_types", []):
        if jt and jt not in seen:
            seen.append(jt)
    merged["job_types"] = seen

    logger.debug(f"Merged result: {merged}")
    return merged