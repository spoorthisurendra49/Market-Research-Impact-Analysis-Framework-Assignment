import streamlit as st
import requests
from datetime import date

API_BASE = "http://127.0.0.1:8000"

# -------------------------
# Page Config
# -------------------------
st.set_page_config(
    page_title="Market Intelligence AI",
    page_icon="📊",
    layout="wide"
)

# -------------------------
# Custom CSS (Futuristic UI)
# -------------------------
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 16px;
    border-radius: 14px;
    text-align: center;
    color: #e5e7eb;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
.section {
    margin-top: 30px;
}
.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: #2563eb;
    color: white;
    margin: 4px 6px 4px 0;
    font-size: 0.85rem;
}
.muted {
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Header
# -------------------------
st.title("📊 Market Intelligence AI")
st.caption("Agentic Market Research System • LangGraph + Ollama + MCP")

# -------------------------
# Sidebar Inputs
# -------------------------
st.sidebar.header("🔍 Analysis Inputs")

industry = st.sidebar.text_input("Company / Industry", value="Reliance Industries")
from_date = st.sidebar.date_input("From Date", value=date(2026, 1, 1))
to_date = st.sidebar.date_input("To Date", value=date(2026, 1, 15))

run_analysis = st.sidebar.button("🚀 Generate Intelligence Report")

# -------------------------
# Run Analysis
# -------------------------
if run_analysis:
    with st.spinner("Running agentic analysis..."):
        payload = {
            "industry": industry,
            "from": str(from_date),
            "to": str(to_date)
        }

        response = requests.post(f"{API_BASE}/analyze", json=payload)

        if response.status_code == 200:
            data = response.json()
            st.session_state["report"] = data["report"]
            st.session_state["report_id"] = data["report_id"]
            st.session_state["duration"] = data.get("duration_seconds")
            st.success("✅ Report generated successfully")
        else:
            st.error("❌ Failed to generate report")

# -------------------------
# Display Report
# -------------------------
if "report" in st.session_state:
    report = st.session_state["report"]

    # -------------------------
    # Metrics Row
    # -------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"<div class='metric-card'><h3>{industry}</h3><p class='muted'>Target</p></div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"<div class='metric-card'><h3>{len(report.get('impact_radar', []))}</h3><p class='muted'>Impact Events</p></div>",
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"<div class='metric-card'><h3>{len(report.get('sources', []))}</h3><p class='muted'>Sources</p></div>",
            unsafe_allow_html=True
        )

    with col4:
        duration = st.session_state.get("duration", "—")
        st.markdown(
            f"<div class='metric-card'><h3>{duration}s</h3><p class='muted'>Execution Time</p></div>",
            unsafe_allow_html=True
        )

    # -------------------------
    # Summary
    # -------------------------
    st.markdown("<div class='section'></div>", unsafe_allow_html=True)
    st.subheader("📌 Executive Summary")
    st.write(report.get("summary", ""))

    # -------------------------
    # Drivers
    # -------------------------
    st.subheader("🚀 Key Drivers")
    drivers = report.get("drivers", [])
    if drivers:
        for d in drivers:
            st.markdown(f"<span class='badge'>{d}</span>", unsafe_allow_html=True)
    else:
        st.info("No explicit drivers identified from analyzed sources.")

    # -------------------------
    # Competitors
    # -------------------------
    st.subheader("🏢 Competitors (Evidence-based)")
    competitors = report.get("competitors", [])
    if competitors:
        for c in competitors:
            st.markdown(f"<span class='badge'>{c}</span>", unsafe_allow_html=True)
    else:
        st.warning("No competitors explicitly mentioned in analyzed sources.")

    # -------------------------
    # Risks & Opportunities
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚠️ Risks")
        risks = report.get("risks", [])
        if risks:
            for r in risks:
                st.write(f"- {r}")
        else:
            st.info("No material risks identified.")

    with col2:
        st.subheader("🌱 Opportunities")
        opportunities = report.get("opportunities", [])
        if opportunities:
            for o in opportunities:
                st.write(f"- {o}")
        else:
            st.info("No explicit opportunities identified.")

    # -------------------------
    # Impact Radar
    # -------------------------
    st.subheader("📍 Impact Radar")
    for item in report.get("impact_radar", []):
        with st.expander(item.get("event", "Impact Event")):
            st.write(f"**Impact Level:** {item.get('impact_level')}")
            st.write(f"**Score:** {item.get('score')}")
            st.write("**Why it matters:**")
            for w in item.get("why", []):
                st.write(f"- {w}")
            st.write("**Recommended Actions:**")
            for a in item.get("actions", []):
                st.write(f"- {a}")
            if item.get("url"):
                st.markdown(f"[🔗 Source]({item['url']})")

    # -------------------------
    # 90-Day Plan
    # -------------------------
    st.subheader("🗺️ 90-Day Action Plan (Evidence-backed)")
    plan = report.get("90_day_plan", {})

    if plan:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**0–30 Days**")
            for i in plan.get("0_30", []):
                st.write(f"- {i}")
        with col2:
            st.write("**30–60 Days**")
            for i in plan.get("30_60", []):
                st.write(f"- {i}")
        with col3:
            st.write("**60–90 Days**")
            for i in plan.get("60_90", []):
                st.write(f"- {i}")
    else:
        st.info("No prescriptive 90-day actions were directly supported by the analyzed sources.")

    # -------------------------
    # Sources
    # -------------------------
    st.subheader("📚 Sources")
    for s in report.get("sources", []):
        st.markdown(f"- [Source]({s})")

# -------------------------
# Chat Section
# -------------------------
if "report_id" in st.session_state:
    st.markdown("<div class='section'></div>", unsafe_allow_html=True)
    st.header("💬 Ask Questions About This Report")

    question = st.text_input("Ask a question grounded in this report")

    if st.button("Ask"):
        payload = {
            "report_id": st.session_state["report_id"],
            "question": question
        }

        response = requests.post(f"{API_BASE}/chat", json=payload)

        if response.status_code == 200:
            ans = response.json()
            st.success("Answer:")
            st.write(ans["answer"])
        else:
            st.error("Failed to get answer")
