# ============================================================
# pages/03_recommendations.py — Ranked Action Items
# Premium UI with priority cards and supporting data
# ============================================================

import streamlit as st
from core.ai_engine import generate_recommendations, _rule_based_recommendations

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
        radial-gradient(ellipse 70% 50% at 10% 30%, rgba(99,102,241,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 50% 60% at 90% 70%, rgba(16,185,129,0.08) 0%, transparent 60%);
}
h1,h2,h3 { font-family:'Syne',sans-serif!important; letter-spacing:-0.02em; }
#MainMenu,footer,header { visibility:hidden; }
[data-testid="stSidebar"] { background:rgba(10,12,24,0.95)!important; border-right:1px solid rgba(99,102,241,0.2)!important; }
hr { border:none!important; border-top:1px solid rgba(255,255,255,0.06)!important; }

.section-title {
    font-family:'Syne',sans-serif; font-size:13px; font-weight:700;
    color:#4B5563; letter-spacing:2px; text-transform:uppercase; margin-bottom:14px;
}

/* Priority header */
.priority-header {
    display: flex; align-items: center; gap: 12px;
    margin: 28px 0 14px;
}
.priority-label {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 800;
    letter-spacing: 2px; text-transform: uppercase;
    padding: 4px 14px; border-radius: 20px;
}
.priority-label.urgent  { background:rgba(239,68,68,0.15);  color:#EF4444; border:1px solid rgba(239,68,68,0.3);  }
.priority-label.high    { background:rgba(245,158,11,0.15); color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
.priority-label.opp     { background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
.priority-line { flex:1; height:1px; background:rgba(255,255,255,0.06); }

/* Rec card */
.rec-card {
    border-radius: 14px;
    padding: 20px 24px;
    margin: 10px 0;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.rec-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 40px rgba(0,0,0,0.3);
}
.rec-card.urgent {
    background: rgba(239,68,68,0.06);
    border: 1px solid rgba(239,68,68,0.25);
    border-left: 4px solid #EF4444;
}
.rec-card.high {
    background: rgba(245,158,11,0.06);
    border: 1px solid rgba(245,158,11,0.25);
    border-left: 4px solid #F59E0B;
}
.rec-card.opportunity {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.25);
    border-left: 4px solid #10B981;
}
.rec-title { font-family:'Syne',sans-serif; font-size:15px; font-weight:700; color:#F1F5F9; margin-bottom:8px; }
.rec-desc  { font-size:13px; color:#94A3B8; line-height:1.7; margin-bottom:12px; }
.rec-impact {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
    padding: 4px 12px; border-radius: 20px;
}
.rec-impact.urgent     { background:rgba(239,68,68,0.15);  color:#EF4444; }
.rec-impact.high       { background:rgba(245,158,11,0.15); color:#F59E0B; }
.rec-impact.opportunity{ background:rgba(16,185,129,0.15); color:#10B981; }
.rec-num {
    position: absolute; top: 18px; right: 20px;
    font-family: 'Syne', sans-serif; font-size: 36px; font-weight: 800;
    color: rgba(255,255,255,0.04); line-height:1;
}
</style>
""", unsafe_allow_html=True)

# ── Load default recs ─────────────────────────────────────────
if st.session_state.get("recommendations") is None:
    st.session_state.recommendations = _rule_based_recommendations(findings)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style='padding:20px 0 8px'>
    <p style='font-family:Syne,sans-serif;font-size:26px;font-weight:800;
              color:#F1F5F9;margin:0;letter-spacing:-0.02em'>💡 Recommendations</p>
    <p style='color:#4B5563;font-size:13px;margin:6px 0 0'>
        Data-driven actions ranked by business impact
    </p>
</div>
""", unsafe_allow_html=True)
st.divider()

col_btn1, col_btn2, col_btn3 = st.columns(3)
if col_btn1.button("⚡ Regenerate with AI", type="primary", use_container_width=True):
    with st.spinner("Generating AI recommendations..."):
        st.session_state.recommendations = generate_recommendations(findings, summary)
        st.rerun()
if col_btn2.button("↺ Reset to Rule-Based", use_container_width=True):
    st.session_state.recommendations = _rule_based_recommendations(findings)
    st.rerun()
if col_btn3.button("📋 Copy All to Clipboard", use_container_width=True):
    recs_text = "\n\n".join([
        f"[{r.get('priority','').upper()}] {r.get('title','')}\n{r.get('description','')}\nImpact: {r.get('impact','')}"
        for r in st.session_state.recommendations
    ])
    st.code(recs_text, language=None)

st.divider()

recs = st.session_state.recommendations

# ── Summary strip ─────────────────────────────────────────────
urgent_n = sum(1 for r in recs if str(r.get("priority","")).lower() == "urgent")
high_n   = sum(1 for r in recs if str(r.get("priority","")).lower() == "high")
opp_n    = sum(1 for r in recs if str(r.get("priority","")).lower() == "opportunity")

s1, s2, s3 = st.columns(3)
s1.metric("🔴 Urgent",      urgent_n, help="Act this week")
s2.metric("🟡 High",        high_n,   help="Act this month")
s3.metric("🟢 Opportunity", opp_n,    help="Plan next quarter")
st.divider()

# ── Display by priority ───────────────────────────────────────
PRIORITY_CONFIG = {
    "urgent"     : ("🔴 URGENT",      "urgent", "Act This Week"),
    "high"       : ("🟡 HIGH",        "high",   "Act This Month"),
    "opportunity": ("🟢 OPPORTUNITY", "opp",    "Next Quarter"),
}

global_idx = 0
for priority, (emoji_label, css_class, timeframe) in PRIORITY_CONFIG.items():
    group = [r for r in recs if str(r.get("priority","")).lower() == priority]
    if not group:
        continue

    st.markdown(f"""
    <div class='priority-header'>
        <span class='priority-label {css_class}'>{emoji_label}</span>
        <span style='color:#374151;font-size:12px'>{timeframe}</span>
        <div class='priority-line'></div>
        <span style='color:#374151;font-size:12px'>{len(group)} action{"s" if len(group)>1 else ""}</span>
    </div>""", unsafe_allow_html=True)

    for rec in group:
        global_idx += 1
        st.markdown(f"""
        <div class='rec-card {priority}'>
            <div class='rec-num'>{global_idx:02d}</div>
            <div class='rec-title'>{rec.get('title','Recommendation')}</div>
            <div class='rec-desc'>{rec.get('description','')}</div>
            <span class='rec-impact {priority}'>💰 {rec.get('impact','TBD')}</span>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Supporting data tabs ──────────────────────────────────────
st.markdown("<div class='section-title'>Supporting Data</div>", unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["💸 Discount Analysis", "🗺️ Regional", "👥 Segment", "📦 Category"])

with t1:
    if "Discount_Band" in df.columns:
        d = (
            df.groupby("Discount_Band", observed=True)
              .agg(Orders=("Sales","count"),
                   Avg_Margin=("Profit_Margin_","mean"),
                   Total_Profit=("Profit","sum"),
                   Avg_Sales=("Sales","mean"))
              .reset_index().dropna(subset=["Discount_Band"])
        )
        d = d[d["Discount_Band"].astype(str) != "nan"]
        d["Avg_Margin"]   = d["Avg_Margin"].round(1)
        d["Total_Profit"] = d["Total_Profit"].round(0)
        d["Avg_Sales"]    = d["Avg_Sales"].round(0)
        st.dataframe(d.rename(columns={
            "Discount_Band":"Band","Avg_Margin":"Margin %",
            "Total_Profit":"Total Profit ($)","Avg_Sales":"Avg Sale ($)"}),
            use_container_width=True, hide_index=True)

with t2:
    if "Region" in df.columns:
        r = (
            df.groupby("Region")
              .agg(Sales=("Sales","sum"), Profit=("Profit","sum"),
                   Margin=("Profit_Margin_","mean"), Orders=("Sales","count"))
              .reset_index().sort_values("Sales", ascending=False)
        )
        r["Sales"]  = r["Sales"].round(0)
        r["Profit"] = r["Profit"].round(0)
        r["Margin"] = r["Margin"].round(1)
        st.dataframe(r.rename(columns={
            "Sales":"Revenue ($)","Profit":"Profit ($)","Margin":"Margin %"}),
            use_container_width=True, hide_index=True)

with t3:
    if "Segment" in df.columns:
        s = (
            df.groupby("Segment")
              .agg(Sales=("Sales","sum"), Profit=("Profit","sum"),
                   Margin=("Profit_Margin_","mean"), Avg_Order=("Sales","mean"))
              .reset_index().sort_values("Sales", ascending=False)
        )
        s["Sales"]     = s["Sales"].round(0)
        s["Profit"]    = s["Profit"].round(0)
        s["Margin"]    = s["Margin"].round(1)
        s["Avg_Order"] = s["Avg_Order"].round(0)
        st.dataframe(s.rename(columns={
            "Sales":"Revenue ($)","Profit":"Profit ($)",
            "Margin":"Margin %","Avg_Order":"Avg Order ($)"}),
            use_container_width=True, hide_index=True)

with t4:
    if "Category" in df.columns:
        c = (
            df.groupby("Category")
              .agg(Sales=("Sales","sum"), Profit=("Profit","sum"),
                   Margin=("Profit_Margin_","mean"))
              .reset_index().sort_values("Profit", ascending=False)
        )
        c["Sales"]  = c["Sales"].round(0)
        c["Profit"] = c["Profit"].round(0)
        c["Margin"] = c["Margin"].round(1)
        st.dataframe(c.rename(columns={
            "Sales":"Revenue ($)","Profit":"Profit ($)","Margin":"Margin %"}),
            use_container_width=True, hide_index=True)
