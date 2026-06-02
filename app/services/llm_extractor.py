# ---------------------------------------------------------------------------
# llm_extractor.py
# Supports Groq API (production) and Ollama (local fallback).
# ---------------------------------------------------------------------------

import json
import logging
import re
import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
try:
    from app.config import (
        GROQ_API_KEY, GROQ_MODEL, GROQ_URL,
        USE_GROQ, OLLAMA_MODEL
    )
except ImportError:
    GROQ_API_KEY = ""
    GROQ_MODEL   = "llama-3.3-70b-versatile"
    GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
    USE_GROQ     = True
    OLLAMA_MODEL = "qwen2.5:7b"

OLLAMA_URL  = "http://localhost:11434/api/generate"
MAX_RETRIES = 2
TIMEOUT     = 30.0

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """Ekstrak info renovasi dari teks Indonesia. Kembalikan HANYA JSON valid.

Skema:
{{"job_types":[],"area_m2":null,"quality":null,"location":null,"scope":null,"room":null}}

job_types (array, ambil SEMUA yang relevan):
"painting"→cat/ngecat/repaint/pengecatan
"ceramic"→keramik lantai/ubin lantai/granit lantai
"wall_tile"→keramik dinding/tile dinding/mozaik dinding
"ceiling"→plafon/plafond/eternit/gypsum ceiling/langit-langit
"wall"→plester/aci/acian/dinding retak/tambal dinding
"electrical"→listrik/kabel/stopkontak/titik lampu/instalasi listrik
"plumbing"→pipa/kran/toilet/closet/wastafel/shower/saluran air
"roofing"→atap bocor/genteng/talang/rangka atap
"waterproofing"→waterproof/anti bocor/coating/pelapis dak
"carpentry"→pintu kayu/daun pintu/kusen kayu/partisi kayu
"window"→jendela/teralis/kusen aluminium/UPVC
"flooring_wood"→lantai kayu/parket/vinyl lantai/SPC/laminate
"cabinet"→lemari/wardrobe/built-in/rak dinding
"carport"→kanopi/carport/garasi/polycarbonate
"fence"→pagar/pagar bata/pagar besi/tembok pagar
"demolition"→bongkar/robohkan/rombak/kupas
"insulation"→insulasi/peredam panas/glasswool/rockwool
"wallpaper"→wallpaper/wall panel/wainscoting/vinyl wall

Aturan:
- plafon→"ceiling" BUKAN "carpentry"
- jendela→"window" BUKAN "carpentry"
- keramik dinding→"wall_tile", keramik lantai→"ceramic"
- vinyl/parket→"flooring_wood" BUKAN "ceramic"
- lemari/wardrobe→"cabinet" BUKAN "carpentry"
- kanopi→"carport" BUKAN "roofing"
- quality: premium/mewah/bagus→"premium", ekonomi/murah→"ekonomi", standar/normal→"standar"
- scope: total/full/bongkar semua→"full", touch up/ringan→"light"
- dimensi 4x5/4mx5m→area_m2=20
- room: kamar mandi→"bathroom", dapur→"kitchen", kamar tidur→"bedroom", ruang tamu→"living_room", atap→"roof"
- EKSTRAK HANYA job type yang EKSPLISIT disebutkan. JANGAN infer "wall", "cabinet" dari "renovasi total"

Contoh:
Input: "cat ulang kamar tidur 12m2, ganti plafon gypsum, pasang vinyl lantai"
Output: {{"job_types":["painting","ceiling","flooring_wood"],"area_m2":12,"quality":null,"location":null,"scope":null,"room":"bedroom"}}

Input: "renovasi total kamar mandi 3x2m premium Surabaya, bongkar semua"
Output: {{"job_types":["plumbing","ceramic","wall_tile","electrical","waterproofing","ceiling","demolition"],"area_m2":6,"quality":"premium","location":"surabaya","scope":"full","room":"bathroom"}}

Input: "{text}"
JSON:"""

# ---------------------------------------------------------------------------
# Keyword validation
# ---------------------------------------------------------------------------
JOB_KEYWORDS: dict[str, list[str]] = {
    "painting":      ["cat ", "ngecat", "repaint", "poles", "pengecatan", "warna tembok"],
    "ceramic":       ["keramik lantai", "ubin lantai", "granit lantai", "ganti lantai keramik"],
    "wall_tile":     ["keramik dinding", "ubin dinding", "tile dinding", "mozaik dinding"],
    "ceiling":       ["plafon", "plafond", "eternit", "gypsum board", "langit-langit"],
    "wall":          ["plester", " aci ", "acian", "dinding retak", "tambal dinding"],
    "electrical":    ["listrik", "kabel listrik", "stopkontak", "titik lampu", "kelistrikan", "perlampu"],
    "plumbing":      ["pipa", "kran", "wastafel", "toilet", "closet", "saluran air", "shower"],
    "roofing":       ["atap", "genteng", "talang", "rangka atap"],
    "waterproofing": ["waterproof", "anti bocor", "coating", "pelapis dak", "bocor dak"],
    "carpentry":     ["pintu", "kusen", "daun pintu", "ganti pintu", "partisi kayu"],
    "window":        ["jendela", "teralis", "kusen jendela", "bouvenlight"],
    "flooring_wood": ["lantai kayu", "parket", "vinyl lantai", "spc floor", "laminate", "lantai vinyl"],
    "cabinet":       ["lemari", "wardrobe", "built-in", "rak dinding", "kabinet dinding"],
    "carport":       ["kanopi", "carport", "garasi", "polycarbonate", "pergola"],
    "fence":         ["pagar", "tembok pagar", "bikin pagar"],
    "demolition":    ["bongkar", "robohkan", "rombak", "kupas", "demolisi"],
    "insulation":    ["insulasi", "peredam panas", "glasswool", "rockwool"],
    "wallpaper":     ["wallpaper", "wall panel", "wainscoting", "vinyl wall"],
}

FLOOR_KEYWORDS_WOOD = ["vinyl", "parket", "kayu", "spc", "laminate", "wood"]
FLOOR_KEYWORDS_ANY  = ["ganti lantai", "lantai baru", "pasang lantai"]


def _validate_and_enrich_job_types(job_types: list[str], text: str) -> list[str]:
    text_lower = text.lower()
    result = []

    for jt in job_types:
        keywords = JOB_KEYWORDS.get(jt, [])
        if not keywords or any(kw in text_lower for kw in keywords):
            result.append(jt)
        else:
            logger.info(f"[keyword-filter] Removed '{jt}' — no keyword in text")

    for jt, keywords in JOB_KEYWORDS.items():
        if jt not in result and any(kw in text_lower for kw in keywords):
            result.append(jt)
            logger.info(f"[keyword-filter] Added missed '{jt}'")

    if any(kw in text_lower for kw in FLOOR_KEYWORDS_ANY):
        has_wood = any(kw in text_lower for kw in FLOOR_KEYWORDS_WOOD)
        if has_wood and "flooring_wood" not in result:
            result.append("flooring_wood")
        elif not has_wood and "ceramic" not in result and "flooring_wood" not in result:
            result.append("ceramic")

    seen = []
    for jt in result:
        if jt not in seen:
            seen.append(jt)
    return seen


# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------
def _parse_llm_response(raw: str) -> dict | None:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ---------------------------------------------------------------------------
# Groq API call
# ---------------------------------------------------------------------------
def _extract_via_groq(text: str) -> dict | None:
    if not GROQ_API_KEY:
        logger.warning("Groq API key not set — skipping Groq")
        return None

    prompt = EXTRACTION_PROMPT.format(text=text)

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            logger.debug(f"Groq extraction attempt {attempt}")
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(
                    GROQ_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type":  "application/json",
                    },
                    json={
                        "model":       GROQ_MODEL,
                        "messages":    [
                            {
                                "role":    "system",
                                "content": "Kamu adalah sistem ekstraksi data renovasi. Selalu kembalikan JSON valid saja, tanpa penjelasan."
                            },
                            {
                                "role":    "user",
                                "content": prompt,
                            }
                        ],
                        "temperature":  0.1,
                        "max_tokens":   512,
                    },
                )
                response.raise_for_status()
                data     = response.json()
                raw_text = data["choices"][0]["message"]["content"]

            parsed = _parse_llm_response(raw_text)
            if parsed:
                logger.info(f"Groq extraction success attempt {attempt}: {parsed}")
                return parsed
            else:
                logger.warning(f"Groq attempt {attempt} unparseable: {raw_text[:100]}")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Groq rate limit hit — falling back to Ollama")
                return None
            logger.warning(f"Groq HTTP error {e.response.status_code}: {e}")
        except httpx.TimeoutException:
            logger.warning(f"Groq attempt {attempt} timed out")
        except Exception as e:
            logger.warning(f"Groq attempt {attempt} failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Ollama API call (fallback)
# ---------------------------------------------------------------------------
def _extract_via_ollama(text: str) -> dict | None:
    prompt = EXTRACTION_PROMPT.format(text=text)

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            logger.debug(f"Ollama extraction attempt {attempt}")
            with httpx.Client(timeout=240.0) as client:
                response = client.post(
                    OLLAMA_URL,
                    json={
                        "model":   OLLAMA_MODEL,
                        "prompt":  prompt,
                        "stream":  False,
                        "options": {"temperature": 0.1, "top_p": 0.9},
                    },
                )
                response.raise_for_status()
                raw_text = response.json().get("response", "")

            parsed = _parse_llm_response(raw_text)
            if parsed:
                logger.info(f"Ollama extraction success attempt {attempt}: {parsed}")
                return parsed

        except httpx.ConnectError:
            logger.warning("Ollama not reachable")
            return None
        except httpx.TimeoutException:
            logger.warning(f"Ollama attempt {attempt} timed out")
        except Exception as e:
            logger.warning(f"Ollama attempt {attempt} failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------
def extract_from_text(text: str) -> dict | None:
    """
    Extract renovation data from Indonesian text.
    Uses Groq API if available, falls back to Ollama.
    """
    parsed = None

    # Try Groq first (production)
    if USE_GROQ and GROQ_API_KEY:
        logger.info("Using Groq API for extraction")
        parsed = _extract_via_groq(text)

    # Fallback to Ollama (local)
    if parsed is None:
        logger.info("Falling back to Ollama for extraction")
        parsed = _extract_via_ollama(text)

    if parsed is None:
        return None

    # Post-process: calculate area from dimensions
    if not parsed.get("area_m2"):
        dim_pattern = r"(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*m?"
        match = re.search(dim_pattern, text)
        if match:
            parsed["area_m2"] = float(match.group(1)) * float(match.group(2))

    # Validate and enrich job types
    if "job_types" in parsed and isinstance(parsed["job_types"], list):
        original = parsed["job_types"][:]
        parsed["job_types"] = _validate_and_enrich_job_types(parsed["job_types"], text)
        if parsed["job_types"] != original:
            logger.info(f"[keyword-filter] {original} → {parsed['job_types']}")

    logger.info(f"Final extraction: {parsed}")
    return parsed


# ---------------------------------------------------------------------------
# Merge helper
# ---------------------------------------------------------------------------
def merge_llm_with_parsed(llm_result: dict | None, parsed_fields: dict) -> dict:
    if not llm_result:
        return parsed_fields

    merged = dict(llm_result)
    for key, value in parsed_fields.items():
        if value is not None:
            merged[key] = value

    if "job_types" not in merged or not merged["job_types"]:
        single = merged.get("job_type")
        merged["job_types"] = [single] if single else []

    seen = []
    for jt in merged.get("job_types", []):
        if jt and jt not in seen:
            seen.append(jt)
    merged["job_types"] = seen

    return merged