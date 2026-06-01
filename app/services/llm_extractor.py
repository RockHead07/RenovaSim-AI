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

EXTRACTION_PROMPT = """Anda adalah sistem ekstraksi informasi renovasi rumah Indonesia yang sangat akurat.
Tugas: Ekstrak informasi terstruktur dari deskripsi renovasi pengguna.
Kembalikan HANYA JSON valid. Tanpa penjelasan, tanpa markdown, tanpa blok kode.

Skema output:
{{
  "job_types": [...],
  "area_m2": number | null,
  "quality": "ekonomi" | "standar" | "premium" | null,
  "location": string | null,
  "scope": "light" | "medium" | "full" | null,
  "room": "bathroom" | "kitchen" | "bedroom" | "living_room" | "roof" | null
}}

JOB TYPES valid (pilih SEMUA yang relevan dari deskripsi):
- "painting"       → cat dinding, cat plafon, ngecat, repaint, cat ulang, poles, warna tembok, cat eksterior, cat interior, pengecatan
- "ceramic"        → keramik lantai, ubin lantai, granit lantai, ganti lantai keramik, pasang lantai keramik, homogeneous tile lantai
- "wall_tile"      → keramik dinding, ubin dinding, tile dinding, pasang keramik dinding, keramik kamar mandi (dinding), mozaik dinding
- "ceiling"        → plafon, plafond, eternit, gypsum board, GRC board, drop ceiling, plafon jebol, plafon bocor, ganti plafon, pasang plafon, langit-langit
- "wall"           → plester, aci, acian, plesteran dinding, dinding retak, tambal dinding, perbaiki dinding, screeding, nat plester
- "electrical"     → listrik, kabel listrik, stopkontak, saklar, MCB, panel listrik, instalasi listrik, titik lampu, grounding, daya listrik
- "plumbing"       → pipa air, kran, wastafel, toilet, closet, saluran air, bak mandi, shower, water heater, pompa air, septik tank
- "roofing"        → atap bocor, genteng, talang air, rangka atap, baja ringan, asbes atap, renovasi atap, ganti genteng
- "waterproofing"  → waterproof, anti bocor, coating anti air, pelapis dak, bocor dak beton, sealant, injeksi beton
- "carpentry"      → pintu kayu, kusen pintu kayu, daun pintu, ganti pintu (kayu/PVC), partisi kayu, panel kayu
- "window"         → jendela, kusen jendela, ganti jendela, teralis, jalusi, jendela aluminium, jendela UPVC, kaca jendela, bouvenlight
- "flooring_wood"  → lantai kayu, parket, vinyl lantai, SPC floor, laminate floor, floor ing kayu, wood floor, lantai vinyl
- "cabinet"        → lemari, wardrobe, lemari tanam, lemari pakaian, lemari built-in, rak dinding, kabinet dinding, lemari custom
- "carport"        → kanopi, carport, garasi atap, kanopi baja ringan, atap polycarbonate, atap garasi, pergola
- "fence"          → pagar, pagar bata, pagar besi, pagar tembok, pagar hollow, bikin pagar, tembok pagar, pagar depan rumah
- "demolition"     → bongkar, bongkaran, robohkan, hancurkan, demolisi, buka dinding, buang dinding lama, rombak, kupas
- "insulation"     → insulasi, peredam panas, peredam suara, glasswool, rockwool, foam insulasi, atap panas, aluminium foil atap
- "wallpaper"      → wallpaper, wall panel, wainscoting, panel dinding, wallcovering, stiker dinding dekoratif, vinyl wall

ATURAN KRITIS (jangan sampai salah):
- "plafon/plafond/eternit/gypsum langit-langit" → "ceiling" (BUKAN "carpentry")
- "jendela/kusen jendela/teralis" → "window" (BUKAN "carpentry")
- "keramik dinding/mozaik dinding" → "wall_tile" (BUKAN "ceramic")
- "keramik lantai/granit lantai" → "ceramic" (BUKAN "wall_tile")
- "lantai vinyl/parket/kayu" → "flooring_wood" (BUKAN "ceramic")
- "lemari/wardrobe/rak built-in" → "cabinet" (BUKAN "carpentry")
- "kanopi/carport/garasi atap" → "carport" (BUKAN "roofing")
- "bongkar/demolisi" → "demolition" (tambahkan selain job type utama)
- "pagar" → "fence" (BUKAN "carpentry")
- Quality: "premium/mewah/bagus/berkualitas/impor/branded/kelas atas" → "premium"
- Quality: "ekonomi/murah/biasa/seadanya/budget" → "ekonomi"
- Quality: "standar/normal/sedang/menengah" → "standar"
- Scope: "total/full/semua/bongkar semua/rombak total/dari nol" → "full"
- Scope: "touch up/sedikit/ringan/minor/sebagian kecil" → "light"
- Dimensi "4x5", "4mx5m", "4 x 5 meter", "4 kali 5" → area_m2 = 20
- Budget/harga yang disebutkan → ABAIKAN, jangan jadikan job type

CONTOH (few-shot):
Input: "cat ulang kamar tidur 12m2, ganti plafon gypsum, pasang vinyl lantai"
Output: {{"job_types": ["painting", "ceiling", "flooring_wood"], "area_m2": 12, "quality": null, "location": null, "scope": null, "room": "bedroom"}}

Input: "renovasi total kamar mandi 3x2m premium di Surabaya"
Output: {{"job_types": ["plumbing", "ceramic", "wall_tile", "electrical", "waterproofing", "ceiling"], "area_m2": 6, "quality": "premium", "location": "surabaya", "scope": "full", "room": "bathroom"}}

Input: "bikin pagar tembok depan rumah 10m, bongkar pagar lama dulu"
Output: {{"job_types": ["fence", "demolition"], "area_m2": null, "quality": null, "location": null, "scope": null, "room": null}}

Input: "pasang wallpaper kamar anak, lemari built-in, cat dinding warna pastel, 4x4 meter"
Output: {{"job_types": ["wallpaper", "cabinet", "painting"], "area_m2": 16, "quality": null, "location": null, "scope": null, "room": "bedroom"}}

Input: "plafon kamar bocor jebol, dinding retak-retak, mau sekalian pasang insulasi biar ga panas, 20m2"
Output: {{"job_types": ["ceiling", "wall", "insulation"], "area_m2": 20, "quality": null, "location": null, "scope": null, "room": null}}

Input teks renovasi: "{text}"

JSON output:"""


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