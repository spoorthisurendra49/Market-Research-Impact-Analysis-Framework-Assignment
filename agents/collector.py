import ollama
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import List
import time
from mcp_server.server import log

MAX_QUERIES = 2
MAX_URLS = 5
HTTP_TIMEOUT = 4


def _bing_rss_search(query: str) -> List[str]:
    urls = []
    try:
        rss_url = f"https://www.bing.com/news/search?q={query}&format=rss"
        r = requests.get(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=HTTP_TIMEOUT
        )
        root = ET.fromstring(r.text)
        for item in root.findall(".//item"):
            link = item.find("link")
            if link is not None and link.text:
                urls.append(link.text.strip())
    except Exception as e:
        log("Collector", f"Bing RSS error: {e}")
    return urls


def _duckduckgo_search(query: str) -> List[str]:
    urls = []
    try:
        url = f"https://duckduckgo.com/html/?q={query}"
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=HTTP_TIMEOUT
        )
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and "duckduckgo.com" not in href:
                urls.append(href)
    except Exception as e:
        log("Collector", f"DDG error: {e}")
    return urls


def collector_agent(state: dict, tools: dict):
    start = time.time()
    log("Collector", "START")

    industry = state.get("industry")
    if not industry:
        raise RuntimeError("Collector: industry missing")

    prompt = f"""
You are a senior market research analyst.

Industry: {industry}
Country: India

Generate EXACTLY 4 web search queries focusing on:
- regulation
- competitors
- market trends
- risks

Rules:
- One query per line
- No numbering
- No explanation
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        options={"num_predict": 150, "temperature": 0.2}
    )

    raw = response["message"]["content"]
    queries = [q.strip() for q in raw.split("\n") if len(q.strip()) > 6]
    queries = queries[:MAX_QUERIES]

    # Hard fallback queries
    queries.extend([
        f"{industry} RBI regulation India",
        f"{industry} major companies India"
    ])

    urls: List[str] = []

    for q in queries:
        if len(urls) >= MAX_URLS:
            break

       
        urls.extend(_bing_rss_search(q))

        urls = tools["dedupe_items"](urls)

    if not urls:
        raise RuntimeError("Collector produced zero URLs")

    log("Collector", f"END | {round(time.time() - start, 2)} sec")

    return {
        **state,
        "queries": queries,
        "urls": urls[:MAX_URLS]
    }
