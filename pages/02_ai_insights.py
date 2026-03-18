# ============================================================
# pages/02_ai_insights.py — AI Analysis + Q&A
# Premium UI with animated cards and live Q&A history
# ============================================================

import streamlit as st
import os
from core.ai_engine import (generate_executive_summary,
                             answer_question, sanitize_input)

if "df_clean" not in st.session_state or st.session_state.df_clean is None:
    st.warning("⚠️ No data loaded. Go to the Home page first.")
    st.page_link("app.py", label="← Go Home")
    st.stop()

df       = st.session_state.df_clean
findings = st.session_state.get("findings", {})
summary  = st.session_state.get("df_summary", {})

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
.stApp { background:#050810; font-family:'DM Sans',sans-serif; }
.stApp::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
    background:
        radial-gradient(ellipse 70% 50% at 15% 20%, rgba(99,102,241,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 50% 70% at 85% 75%, rgba(16,185,129,0.08) 0%, transparent 60%);
}
h1,h2,h3 { font-family:'Syne',sans-serif!important; letter-spacing:-0.02em; }
#MainMenu,footer,header { visibility:hidden; }
[data-testid="stSidebar"] { background:rgba(10,12,24,0.95)!important; border-right:1px solid rgba(99,102,241,0.2)!important; }
[data-testid="stMetric"] { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:12px; padding:16px!important; }
[data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; font-size:22px!important; color:#F1F5F9!important; }
[data-testid="stMetricLabel"] { color:#64748B!important; font-size:12px!important; }
hr { border:none!important; border-top:1px solid rgba(255,255,255,0.06)!important; }

.section-title {
    font-family:'Syne',sans-serif; font-size:13px; font-weight:700;
    color:#4B5563; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px;
}

/* AI summary box */
.ai-summary-box {
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(16,185,129,0.05));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 28px 32px;
    position: relative;
    overflow: hidden;
    line-height: 1.8;
    color: #CBD5E1;
    font-size: 15px;
}
.ai-summary-box::before {
    content: '✦ AI';
    position: absolute;
    top: 16px; right: 20px;
    font-size: 10px;
    color: #6366F1;
    letter-spacing: 2px;
    font-weight: 700;
}
.ai-summary-box::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6366F1, #10B981, #F59E0B);
}

/* Finding row */
.finding-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.finding-label { font-size: 12px; color: #4B5563; font-weight: 500; }
.finding-value {
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    color: #A5B4FC;
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 6px;
    padding: 3px 10px;
}

/* Alert bars */
.alert-bar {
    border-radius: 10px; padding: 12px 18px;
    font-size: 13px; margin: 6px 0;
    display: flex; align-items: center; gap: 10px;
}
.alert-bar.danger  { background:rgba(239,68,68,0.08);  border:1px solid rgba(239,68,68,0.25);  color:#FCA5A5; }
.alert-bar.warning { background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.25); color:#FCD34D; }
.alert-bar.success { background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25); color:#6EE7B7; }

/* Suggestion pills */
.suggestion-pill {
    display: inline-block;
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 12px;
    color: #A5B4FC;
    cursor: pointer;
    transition: all 0.2s;
    margin: 3px;
}
.suggestion-pill:hover {
    background: rgba(99,102,241,0.18);
    border-color: rgba(99,102,241,0.4);
}

/* Q&A card */
.qa-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
    transition: border-color 0.2s;
}
.qa-card:hover { border-color: rgba(99,102,241,0.3); }
.qa-q { font-size: 13px; color: #6366F1; font-weight: 600; margin-bottom: 8px; }
.qa-a { font-size: 14px; color: #CBD5E1; line-height: 1.7; }

/* Key badge */
.key-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.25);
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; color: #10B981; font-weight: 600;
    letter-spacing: 0.5px;
}
.no-key-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25);
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; color: #F59E0B; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


def _has_key() -> bool:
    try:
        secret_g = st.secrets.get("GEMINI_API_KEY", "")
        secret_q = st.secrets.get("GROQ_API_KEY", "")
    except (KeyError, FileNotFoundError, AttributeError):
        secret_g = secret_q = ""
    return bool(
        st.session_state.get("GEMINI_API_KEY") or
        st.session_state.get("GROQ_API_KEY")   or
        os.getenv("GEMINI_API_KEY")             or
        os.getenv("GROQ_API_KEY")               or
        secret_g or secret_q
    )


# ── Header ────────────────────────────────────────────────────
has_key = _has_key()

st.markdown("""
<div style='padding:20px 0 8px'>
    <p style='font-family:Syne,sans-serif;font-size:26px;font-weight:800;
              color:#F1F5F9;margin:0;letter-spacing:-0.02em'>🤖 AI Insights</p>
    <p style='color:#4B5563;font-size:13px;margin:6px 0 0'>
        Gemini Flash → Groq Llama 3.3 → Rule-based fallback
    </p>
</div>
""", unsafe_allow_html=True)

# AI key status
if has_key:
    st.markdown("<span class='key-badge'>⚡ AI Active</span>", unsafe_allow_html=True)
else:
    st.markdown("<span class='no-key-badge'>⚠️ No API Key — add one in sidebar</span>", unsafe_allow_html=True)

st.divider()

# ── KPI strip ─────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Revenue",       f"${findings.get('total_revenue',0):,.0f}")
m2.metric("📊 Margin",        f"{findings.get('overall_margin_%',0):.1f}%")
m3.metric("📦 Campaign Lift", f"{findings.get('campaign_lift_%',0):+.1f}%")
m4.metric("📅 Peak Month",    findings.get("peak_month","N/A"))
st.divider()

# ── Main layout ───────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<div class='section-title'>Executive Summary</div>", unsafe_allow_html=True)

    if not has_key:
        st.info(
            "🔑 **Add a free API key** in the sidebar → AI Settings.\n\n"
            "- **Gemini**: [aistudio.google.com](https://aistudio.google.com) — 1,500 req/day free\n"
            "- **Groq**: [console.groq.com](https://console.groq.com) — 100 req/day free"
        )

    if st.button("⚡ Generate AI Summary", type="primary", use_container_width=True):
        with st.spinner("Thinking..."):
            st.session_state.ai_summary = generate_executive_summary(findings)

    if st.session_state.get("ai_summary"):
        st.markdown(
            f"<div class='ai-summary-box'>{st.session_state.ai_summary}</div>",
            unsafe_allow_html=True
        )
        # ── New: Download summary ──
        st.download_button(
            "⬇️ Download Summary",
            data=st.session_state.ai_summary.encode("utf-8"),
            file_name="ai_summary.txt",
            mime="text/plain",
            use_container_width=True,
        )
    elif has_key:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.08);
                    border-radius:12px;padding:40px;text-align:center;color:#374151'>
            Click above to generate your AI executive summary
        </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='section-title'>Key Findings</div>", unsafe_allow_html=True)
    pairs = [
        ("Best Region",        findings.get("best_region",        "N/A")),
        ("Worst Region",       findings.get("worst_region",       "N/A")),
        ("Best Segment",       findings.get("best_segment",       "N/A")),
        ("Best Category",      findings.get("best_category",      "N/A")),
        ("Worst Category",     findings.get("worst_category",     "N/A")),
        ("Peak Month",         findings.get("peak_month",         "N/A")),
        ("Low Month",          findings.get("low_month",          "N/A")),
        ("Best Discount Band", findings.get("best_discount_band", "N/A")),
        ("Avg Delivery",       f"{findings.get('avg_delivery_days',0):.1f}d"),
    ]
    rows_html = "".join([
        f"<div class='finding-row'><span class='finding-label'>{lbl}</span>"
        f"<span class='finding-value'>{val}</span></div>"
        for lbl, val in pairs
    ])
    st.markdown(f"<div>{rows_html}</div>", unsafe_allow_html=True)

    st.markdown("<br><div class='section-title'>Alerts</div>", unsafe_allow_html=True)

    margin   = findings.get("overall_margin_%",  0)
    camp_pct = findings.get("campaign_orders_%", 0)
    lift     = findings.get("campaign_lift_%",   0)
    yoy      = findings.get("yoy_growth_%",      None)

    cls = "danger" if margin < 10 else "warning" if margin < 15 else "success"
    ico = "🔴" if margin < 10 else "🟡" if margin < 15 else "🟢"
    st.markdown(f"<div class='alert-bar {cls}'>{ico} Margin: {margin:.1f}%</div>", unsafe_allow_html=True)

    if camp_pct > 60:
        st.markdown(f"<div class='alert-bar warning'>🟡 {camp_pct:.0f}% orders discounted</div>", unsafe_allow_html=True)
    if lift < 0:
        st.markdown(f"<div class='alert-bar danger'>🔴 Lift: {lift:.1f}%</div>", unsafe_allow_html=True)
    elif lift > 10:
        st.markdown(f"<div class='alert-bar success'>🟢 Lift: {lift:+.1f}%</div>", unsafe_allow_html=True)
    if yoy is not None:
        cls2 = "success" if yoy > 0 else "warning"
        st.markdown(f"<div class='alert-bar {cls2}'>{'🟢' if yoy>0 else '🟡'} YoY: {yoy:+.1f}%</div>", unsafe_allow_html=True)

st.divider()

# ── Q&A Section ───────────────────────────────────────────────
st.markdown("<div class='section-title'>Ask Your Data</div>", unsafe_allow_html=True)
st.caption("Natural language questions answered from your actual numbers")

# Suggestion buttons
suggestions = [
    "Which region generates the most profit?",
    "Are my discounts making or losing money?",
    "What is my best performing category?",
    "Which segment has the highest order value?",
    "What month should I run my biggest campaign?",
    "How do campaign orders compare to non-campaign?",
]
sc = st.columns(3)
for i, q in enumerate(suggestions):
    if sc[i % 3].button(q, key=f"sq_{i}", use_container_width=True):
        st.session_state["pending_question"] = q

pending = st.session_state.get("pending_question", "")
if "pending_question" in st.session_state:
    del st.session_state["pending_question"]

user_q = st.text_input(
    "Your question",
    value=pending,
    placeholder="e.g. Which region has the highest profit margin?",
)

col_ask, col_clear = st.columns([3, 1])
with col_ask:
    ask_clicked = st.button("💬 Get Answer", type="primary", use_container_width=True)
with col_clear:
    if st.button("🗑 Clear History", use_container_width=True):
        st.session_state.qa_history = []
        st.rerun()

if ask_clicked and user_q.strip():
    clean_q = sanitize_input(user_q)
    if clean_q != user_q.strip():
        st.warning("Question was sanitized for safety.")
    with st.spinner("Analysing..."):
        answer = answer_question(clean_q, findings, summary)
        if "qa_history" not in st.session_state:
            st.session_state.qa_history = []
        st.session_state.qa_history.insert(0, {"q": user_q, "a": answer})

# ── Q&A history ───────────────────────────────────────────────
if st.session_state.get("qa_history"):
    st.markdown(f"<div class='section-title'>Answer History ({len(st.session_state.qa_history)})</div>", unsafe_allow_html=True)
    for i, item in enumerate(st.session_state.qa_history[:8]):
        st.markdown(f"""
        <div class='qa-card'>
            <div class='qa-q'>Q: {item['q']}</div>
            <div class='qa-a'>{item['a']}</div>
        </div>""", unsafe_allow_html=True)
