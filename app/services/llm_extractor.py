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
TIMEOUT = 240.0

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
- PENTING: ekstrak HANYA job type yang EKSPLISIT disebutkan user. JANGAN inferring "wall", "cabinet", "window", "fence", "demolition" dari kata "renovasi total" atau "semua". Hanya tambahkan jika user benar-benar menyebutnya.

Contoh:
Input: "cat ulang kamar tidur 12m2, ganti plafon gypsum, pasang vinyl lantai"
Output: {{"job_types":["painting","ceiling","flooring_wood"],"area_m2":12,"quality":null,"location":null,"scope":null,"room":"bedroom"}}

Input: "renovasi total kamar mandi 3x2m premium Surabaya, bongkar semua"
Output: {{"job_types":["plumbing","ceramic","wall_tile","electrical","waterproofing","ceiling","demolition"],"area_m2":6,"quality":"premium","location":"surabaya","scope":"full","room":"bathroom"}}

Input: "{text}"
JSON:"""


# Keyword validation — at least ONE keyword must appear in text
JOB_KEYWORDS: dict[str, list[str]] = {
    "painting":      ["cat ", "ngecat", "repaint", "poles", "pengecatan", "warna tembok", "warna dinding"],
    "ceramic":       ["keramik lantai", "ubin lantai", "granit lantai", "ganti lantai keramik", "pasang lantai keramik"],
    "wall_tile":     ["keramik dinding", "ubin dinding", "tile dinding", "mozaik dinding", "keramik kamar mandi"],
    "ceiling":       ["plafon", "plafond", "eternit", "gypsum board", "langit-langit", "grc board"],
    "wall":          ["plester", " aci ", "acian", "dinding retak", "tambal dinding", "screeding", "plesteran"],
    "electrical":    ["listrik", "kabel listrik", "stopkontak", "titik lampu", "instalasi listrik", "kelistrikan", "perlampu", "lampu pasang", "panel listrik"],
    "plumbing":      ["pipa", "kran", "wastafel", "toilet", "closet", "saluran air", "bak mandi", "shower", "pompa air"],
    "roofing":       ["atap", "genteng", "talang", "rangka atap", "baja ringan", "asbes"],
    "waterproofing": ["waterproof", "anti bocor", "coating", "pelapis dak", "bocor dak", "sealant"],
    "carpentry":     ["pintu", "kusen", "daun pintu", "ganti pintu", "partisi kayu"],
    "window":        ["jendela", "teralis", "kusen jendela", "bouvenlight", "jalusi"],
    "flooring_wood": ["lantai kayu", "parket", "vinyl lantai", "spc floor", "laminate", "lantai vinyl", "wood floor"],
    "cabinet":       ["lemari", "wardrobe", "built-in", "rak dinding", "kabinet dinding", "lemari custom"],
    "carport":       ["kanopi", "carport", "garasi", "polycarbonate", "pergola"],
    "fence":         ["pagar", "tembok pagar", "bikin pagar"],
    "demolition":    ["bongkar", "robohkan", "rombak", "kupas", "demolisi"],
    "insulation":    ["insulasi", "peredam panas", "glasswool", "rockwool", "foam insulasi"],
    "wallpaper":     ["wallpaper", "wall panel", "wainscoting", "vinyl wall"],
}

# Special case: "ganti lantai" alone → ceramic (default) unless vinyl/parket specified
FLOOR_KEYWORDS_WOOD = ["vinyl", "parket", "kayu", "spc", "laminate", "wood"]
FLOOR_KEYWORDS_ANY  = ["ganti lantai", "lantai baru", "pasang lantai"]


def _validate_and_enrich_job_types(job_types: list[str], text: str) -> list[str]:
    """
    Two-pass validation:
    1. Remove job types with no matching keywords in text
    2. Add job types whose keywords ARE in text but LLM missed
    """
    text_lower = text.lower()
    result = []

    # Pass 1: keep only job types with keyword evidence
    for jt in job_types:
        keywords = JOB_KEYWORDS.get(jt, [])
        if not keywords:
            result.append(jt)  # unknown type, keep as-is
            continue
        if any(kw in text_lower for kw in keywords):
            result.append(jt)
        else:
            logger.info(f"[keyword-filter] Removed '{jt}' — no keyword found in text")

    # Pass 2: add missed job types that have keyword evidence
    for jt, keywords in JOB_KEYWORDS.items():
        if jt in result:
            continue
        if any(kw in text_lower for kw in keywords):
            result.append(jt)
            logger.info(f"[keyword-filter] Added missed '{jt}' — keyword found in text")

    # Special case: "ganti lantai" without specific material
    if any(kw in text_lower for kw in FLOOR_KEYWORDS_ANY):
        has_wood = any(kw in text_lower for kw in FLOOR_KEYWORDS_WOOD)
        if has_wood and "flooring_wood" not in result:
            result.append("flooring_wood")
        elif not has_wood and "ceramic" not in result and "flooring_wood" not in result:
            result.append("ceramic")  # default to ceramic if unspecified

    # Deduplicate preserving order
    seen = []
    for jt in result:
        if jt not in seen:
            seen.append(jt)
    return seen


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

                # Validate and enrich job types with keyword matching
                if "job_types" in parsed and isinstance(parsed["job_types"], list):
                    original = parsed["job_types"][:]
                    parsed["job_types"] = _validate_and_enrich_job_types(
                        parsed["job_types"], text
                    )
                    if parsed["job_types"] != original:
                        logger.info(
                            f"[keyword-filter] job_types: {original} → {parsed['job_types']}"
                        )

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