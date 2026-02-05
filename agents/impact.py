from mcp_server.server import log
import time


def impact_agent(state: dict, tools: dict):
    start = time.time()
    log("Impact", "START")

    extracted = state.get("extracted", [])
    industry = state.get("industry", "Unknown")
    impacts = []

    for item in extracted[:3]:
        try:
            text = item.get("text", "")
            if len(text) < 200:
                continue

            impact = tools["impact_score"](
                {
                    "event": text[:200],
                    "url": item.get("url")
                },
                context={"industry": industry}
            )

            impacts.append(impact)

        except Exception as e:
            log("Impact", f"Error: {e}")
            continue

    log("Impact", f"END | {round(time.time() - start, 2)} sec")

    return {
        **state,
        "impacts": impacts
    }
