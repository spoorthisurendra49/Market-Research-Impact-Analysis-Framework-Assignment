from fastapi import APIRouter, HTTPException
from orchestrator.graph import build_graph
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import uuid
import time
import requests
import ollama

router = APIRouter()
graph = build_graph()
REPORT_STORE = {}

EXECUTOR = ThreadPoolExecutor(max_workers=1)
TIMEOUT_SECONDS = 60


@router.post("/analyze")
def analyze(payload: dict):

    if "industry" not in payload:
        raise HTTPException(400, "Missing required field: industry")

    # ---- Ollama health check ----
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
    except Exception:
        raise HTTPException(503, "Ollama is not responding")

    # ---- Run graph with HARD timeout ----
    future = EXECUTOR.submit(graph.invoke, payload)

    try:
        start = time.time()
        result = future.result(timeout=TIMEOUT_SECONDS)
        duration = round(time.time() - start, 2)

    except TimeoutError:
        future.cancel()
        raise HTTPException(
            status_code=504,
            detail="Analysis timed out (graph execution blocked)"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    report_id = str(uuid.uuid4())
    REPORT_STORE[report_id] = result

    return {
        "report_id": report_id,
        "duration_seconds": duration,
        "report": result
    }


# --------------------------------------------------
# CHAT ENDPOINT
# --------------------------------------------------
@router.post("/chat")
def chat(payload: dict):
    """
    Q&A over an existing generated report.
    """

    report_id = payload.get("report_id")
    question = payload.get("question")

    if not report_id or not question:
        raise HTTPException(
            status_code=400,
            detail="report_id and question are required"
        )

    report = REPORT_STORE.get(report_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Invalid report_id"
        )

    prompt = f"""
Answer STRICTLY using the report below.
If the answer is not present, reply:
"Not available in report".

REPORT:
{report}

QUESTION:
{question}
"""

    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
            options={
                "num_predict": 300,
                "temperature": 0.1
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama chat failed: {str(e)}"
        )

    return {
        "answer": response["message"]["content"],
        "citations": report.get("sources", [])
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------
@router.get("/health")
def health():
    """
    Lightweight health check for API + Ollama
    """
    try:
        requests.get(
            "http://localhost:11434/api/tags",
            timeout=2
        )
        ollama_status = "ok"
    except Exception:
        ollama_status = "down"

    return {
        "status": "ok",
        "ollama": ollama_status
    }
