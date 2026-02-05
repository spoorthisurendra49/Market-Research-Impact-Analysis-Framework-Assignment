from mcp_server.server import log
import time


def _normalize_to_string(value):
    """
    Converts LLM outputs (str | dict | other) into safe strings
    so they can be stored in sets and sorted.
    """
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        # Try common keys first
        for k in ["name", "risk", "opportunity", "theme"]:
            if k in value and isinstance(value[k], str):
                return value[k].strip()
        return str(value)

    return str(value)


def writer_agent(state: dict, tools: dict):
    start = time.time()
    log("Writer", "START")

    industry = state.get("industry", "Unknown")
    extracted = state.get("extracted", [])
    impacts = state.get("impacts", [])

    competitors = set()
    risks = set()
    opportunities = set()
    themes = set()
    sources = set()

    # --------------------------------------------------
    # Aggregate extracted entities SAFELY
    # --------------------------------------------------
    for item in extracted:
        entities = item.get("entities", {}) or {}

        for c in entities.get("competitors", []):
            competitors.add(_normalize_to_string(c))

        for r in entities.get("risks", []):
            risks.add(_normalize_to_string(r))

        for o in entities.get("opportunities", []):
            opportunities.add(_normalize_to_string(o))

        for t in entities.get("themes", []):
            themes.add(_normalize_to_string(t))

        url = item.get("url")
        if isinstance(url, str):
            sources.add(url)

    # --------------------------------------------------
    # FINAL SAFETY FALLBACK (NO CRASH)
    # --------------------------------------------------
    if not (competitors or risks or opportunities or themes):
        log("Writer", "No strong signals — using minimal fallback")
        themes.add("Limited publicly available data for the selected period")

    report = {
        "summary": (
            f"This report is generated from verified online sources "
            f"and analyzes the current {industry} industry landscape."
        ),
        "drivers": sorted(themes),
        "competitors": (
    sorted(competitors)
    if competitors
    else ["Not identified in analyzed sources"]
),
        "impact_radar": impacts,
        "opportunities": sorted(opportunities),
        "risks": sorted(risks),
        "90_day_plan": (
    {
        "focus": "Monitor industry developments",
        "actions": [
            "Track regulatory and policy updates",
            "Analyze quarterly sector performance reports",
            "Identify emerging competitors from future disclosures"
        ]
    }
    if impacts
    else {}
),
        "sources": sorted(sources)
    }

    log("Writer", f"END | {round(time.time() - start, 2)} sec")

    return tools["generate_market_report"](report)
