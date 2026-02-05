import ollama
import json
import time
from mcp_server.server import log

MAX_URLS = 1
MAX_TEXT_LENGTH = 800
MIN_TEXT_LENGTH = 120


def extractor_agent(state: dict, tools: dict):
    start = time.time()
    log("Extractor", "START")

    urls = state.get("urls", [])
    extracted = []

    if not urls:
        log("Extractor", "No URLs received")
        urls = []

    for url in urls[:MAX_URLS]:
        try:
            raw = tools["fetch_url"](url)
            if not raw:
                continue

            clean = tools["clean_extract"](raw)
            if not clean or len(clean) < MIN_TEXT_LENGTH:
                continue

            text = clean[:MAX_TEXT_LENGTH]

            prompt = f"""
Extract STRICT JSON in this format:

{{
  "competitors": [],
  "risks": [],
  "opportunities": [],
  "themes": []
}}

Rules:
- Return empty lists if unsure
- Output ONLY JSON

TEXT:
{text}
"""

            response = ollama.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
                options={"num_predict": 200, "temperature": 0.1}
            )

            data = json.loads(response["message"]["content"])

            extracted.append({
                "url": url,
                "text": text,
                "entities": {
                    "competitors": data.get("competitors", []),
                    "risks": data.get("risks", []),
                    "opportunities": data.get("opportunities", []),
                    "themes": data.get("themes", [])
                }
            })

        except Exception as e:
            log("Extractor", f"Error {url}: {e}")
            continue

    # ✅ FINAL FALLBACK (THIS IS THE KEY)
    if not extracted:
        log("Extractor", "No usable content found — using minimal fallback")

        extracted = [{
            "url": None,
            "text": "",
            "entities": {
                "competitors": [],
                "risks": [],
                "opportunities": [],
                "themes": ["Insufficient public data for the selected period"]
            }
        }]

    log("Extractor", f"END | {round(time.time() - start, 2)} sec")

    return {
        **state,
        "extracted": extracted
    }
