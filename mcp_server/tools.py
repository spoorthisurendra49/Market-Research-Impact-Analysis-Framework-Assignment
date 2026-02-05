import requests
import trafilatura
import ollama
import json
import hashlib
import xml.etree.ElementTree as ET
from typing import List, Dict
from mcp_server.server import log


# ==================================================
# WEB SEARCH (STABLE: BING RSS ONLY)
# ==================================================
def search_web(query: str) -> List[str]:
    """
    Stable, bot-friendly web search using Bing RSS.
    DuckDuckGo is intentionally NOT used due to timeouts.
    """
    log("Collector", f"search_web (bing rss): {query}")
    urls = []

    try:
        rss_url = f"https://www.bing.com/news/search?q={query}&format=rss"
        r = requests.get(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=4
        )

        root = ET.fromstring(r.text)
        for item in root.findall(".//item"):
            link = item.find("link")
            if link is not None and link.text:
                urls.append(link.text.strip())

    except Exception as e:
        log("Search error", str(e))

    urls = urls[:5]
    log("Collector", f"Found {len(urls)} URLs")
    return urls


# ==================================================
# FETCH + CLEAN WEB PAGE
# ==================================================
def fetch_url(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        return downloaded or ""
    except Exception:
        return ""


def clean_extract(raw_text: str) -> str:
    try:
        return trafilatura.extract(raw_text) or ""
    except Exception:
        return ""


# ==================================================
# ENTITY EXTRACTION (ROBUST JSON)
# ==================================================
def extract_entities(text: str) -> Dict:
    log("Extractor", "extract_entities")

    prompt = f"""
Extract STRICT JSON in EXACTLY this format:

{{
  "competitors": [],
  "risks": [],
  "opportunities": [],
  "themes": []
}}

Rules:
- competitors: company names only
- risks: regulatory, financial, or operational risks
- opportunities: growth or market opportunities
- themes: high-level drivers
- Output ONLY JSON

TEXT:
{text[:1500]}
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        options={
            "num_predict": 200,
            "temperature": 0.1
        }
    )

    raw = response["message"]["content"].strip()
    log("Extractor raw", raw)

    # 🔑 SAFE JSON EXTRACTION
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("No JSON found")

        data = json.loads(raw[start:end])
        return {
            "competitors": data.get("competitors", []),
            "risks": data.get("risks", []),
            "opportunities": data.get("opportunities", []),
            "themes": data.get("themes", [])
        }

    except Exception as e:
        log("Extractor JSON error", str(e))
        return {
            "competitors": [],
            "risks": [],
            "opportunities": [],
            "themes": []
        }


# ==================================================
# DEDUPLICATION
# ==================================================
def dedupe_items(items: List[str]) -> List[str]:
    seen = set()
    unique = []

    for item in items:
        h = hashlib.md5(item.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            unique.append(item)

    return unique


# ==================================================
# IMPACT SCORING (NON-BLOCKING, SAFE JSON)
# ==================================================
def impact_score(item: dict, context: dict) -> Dict:
    # 🔑 HARD GUARD AGAINST EMPTY / WEAK EVENTS
    if not item.get("event") or len(item["event"].strip()) < 50:
        return {
            "event": item.get("event", ""),
            "impact_level": "Low",
            "score": 0,
            "why": ["Insufficient data for impact assessment"],
            "actions": [],
            "url": item.get("url")
        }

    log("Impact", "impact_score")

    prompt = f"""
Industry: {context.get('industry', 'Unknown')}

Event:
{item['event']}

Return STRICT JSON:
{{
  "impact_level": "High | Medium | Low",
  "score": 0,
  "why": [],
  "actions": []
}}

Rules:
- score: 0–100
- why: 2–3 reasons
- actions: 2–3 actions
- Output ONLY JSON
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        options={
            "num_predict": 200,
            "temperature": 0.1
        }
    )

    raw = response["message"]["content"].strip()
    log("Impact raw", raw)

    # 🔑 SAFE JSON EXTRACTION
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("No JSON found")

        data = json.loads(raw[start:end])
        return {
            "event": item["event"],
            "impact_level": data.get("impact_level", "Medium"),
            "score": data.get("score", 50),
            "why": data.get("why", []),
            "actions": data.get("actions", []),
            "url": item.get("url")
        }

    except Exception as e:
        log("Impact JSON error", str(e))
        return {
            "event": item["event"],
            "impact_level": "Medium",
            "score": 50,
            "why": [],
            "actions": [],
            "url": item.get("url")
        }


# ==================================================
# FINAL REPORT HANDOFF
# ==================================================
def generate_market_report(data: Dict) -> Dict:
    log("Writer", "generate_market_report")
    return data
