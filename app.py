# ============================================================
# app.py — CampaignIQ Main Entry Point
# Premium UI + working page navigation
# ============================================================

import streamlit as st
import pandas as pd
import uuid, logging, os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger(__name__)

st.set_page_config(
    page_title="CampaignIQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help"    : "https://github.com/tensakuro/campaign-iq",
        "Report a bug": "https://github.com/tensakuro/campaign-iq/issues",
        "About"       : "CampaignIQ — Free campaign analytics platform",
    }
)

from core.cleaning import clean_dataframe, validate_dataframe
from core.database import init_db, save_to_db
from core.analysis import compute_findings, get_df_summary

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: #050810;
    font-family: 'DM Sans', sans-serif;
}
.stApp::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
        radial-gradient(ellipse 80% 60% at 20% 10%, rgba(99,102,241,0.15) 0%, transparent 60%),
        radial-gradient(ellipse 60% 80% at 80% 80%, rgba(16,185,129,0.10) 0%, transparent 60%),
        radial-gradient(ellipse 50% 50% at 50% 50%, rgba(245,158,11,0.05) 0%, transparent 70%);
    animation: meshPulse 8s ease-in-out infinite alternate;
}
@keyframes meshPulse { 0% { opacity:0.7; } 100% { opacity:1; } }

[data-testid="stSidebar"] {
    background: rgba(10,12,24,0.95) !important;
    border-right: 1px solid rgba(99,102,241,0.2) !important;
}
[data-testid="stSidebar"] * { color: #E2E8F0 !important; }

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

h1, h2, h3 { font-family: 'Syne', sans-serif !important; letter-spacing: -0.02em; }

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px !important;
}
[data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; font-size:22px!important; color:#F1F5F9!important; }
[data-testid="stMetricLabel"] { color:#64748B!important; font-size:12px!important; }

hr { border:none!important; border-top:1px solid rgba(255,255,255,0.06)!important; }

.kpi-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(16,185,129,0.06));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 14px;
    padding: 20px 22px;
    margin: 6px 0;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
.kpi-card::before {
    content: '';
    position: absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, #6366F1, #10B981, #F59E0B);
    opacity: 0.8;
}
.kpi-card:hover { border-color:rgba(99,102,241,0.5); transform:translateY(-3px); box-shadow:0 20px 40px rgba(99,102,241,0.15); }
.kpi-icon  { font-size:26px; margin-bottom:8px; }
.kpi-value { font-family:'Syne',sans-serif; font-size:18px; font-weight:700; color:#F1F5F9; }
.kpi-label { font-size:11px; color:#64748B; text-transform:uppercase; letter-spacing:1.5px; margin-top:4px; }

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(42px, 6vw, 72px); font-weight: 800;
    background: linear-gradient(135deg, #F1F5F9 30%, #6366F1 60%, #10B981 90%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    line-height: 1.1; letter-spacing: -0.03em; margin: 0;
}
.hero-sub { font-size:18px; color:#64748B; margin-top:16px; font-weight:300; }

.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:11px; font-weight:600; letter-spacing:0.5px; text-transform:uppercase; }
.badge-success { background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
.badge-warning { background:rgba(245,158,11,0.15); color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
.badge-danger  { background:rgba(239,68,68,0.15);  color:#EF4444; border:1px solid rgba(239,68,68,0.3); }

.alert-critical { background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.3); border-left:4px solid #EF4444; border-radius:10px; padding:14px 18px; color:#FCA5A5; font-size:14px; margin:8px 0; }
.alert-warning  { background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3); border-left:4px solid #F59E0B; border-radius:10px; padding:14px 18px; color:#FCD34D; font-size:14px; margin:8px 0; }
.alert-success  { background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.3); border-left:4px solid #10B981; border-radius:10px; padding:14px 18px; color:#6EE7B7; font-size:14px; margin:8px 0; }

.sidebar-brand { text-align:center; padding:12px 0 20px; }
.sidebar-logo  { font-size:40px; display:block; margin-bottom:8px; filter:drop-shadow(0 0 20px rgba(99,102,241,0.6)); }
.sidebar-title { font-family:'Syne',sans-serif; font-size:20px; font-weight:800; color:#F1F5F9; letter-spacing:-0.02em; }
.sidebar-sub   { font-size:11px; color:#4B5563; letter-spacing:2px; text-transform:uppercase; margin-top:4px; }

.stButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
}
.stButton > button:hover { transform:translateY(-1px)!important; box-shadow:0 8px 25px rgba(99,102,241,0.4)!important; }

/* page_link button styling */
[data-testid="stPageLink"] a {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
    display: block !important;
    color: #E2E8F0 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    text-decoration: none !important;
}
[data-testid="stPageLink"] a:hover {
    border-color: rgba(99,102,241,0.4) !important;
    background: rgba(99,102,241,0.08) !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.3) !important;
}

.stat-strip  { display:flex; gap:8px; flex-wrap:wrap; margin:12px 0; }
.stat-chip   { background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2); border-radius:20px; padding:4px 12px; font-size:12px; color:#A5B4FC; }

.feature-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; margin:16px 0; }
.feature-item { background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:14px 16px; font-size:13px; color:#94A3B8; }
.feature-item strong { color:#E2E8F0; display:block; margin-bottom:3px; }
</style>
""", unsafe_allow_html=True)

# ── Session isolation ─────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.update({
        "session_id"     : str(uuid.uuid4())[:8],
        "df_clean"       : None,
        "findings"       : {},
        "df_summary"     : {},
        "clean_report"   : {},
        "last_file_name" : None,
        "ai_summary"     : None,
        "recommendations": None,
        "qa_history"     : [],
    })
    log.info("New session: %s", st.session_state.session_id)

init_db()

MAX_FILE_MB = 50
SAMPLE_PATH = "data/sales_data.csv"


def validate_upload(uploaded_file) -> tuple:
    if uploaded_file.size / 1024 / 1024 > MAX_FILE_MB:
        return False, f"File too large ({uploaded_file.size/1024/1024:.1f} MB). Max {MAX_FILE_MB} MB."
    name = uploaded_file.name.lower()
    if not (name.endswith(".csv") or name.endswith(".xlsx")):
        return False, "Only CSV and Excel (.xlsx) files accepted."
    try:
        uploaded_file.seek(0)
        test = (
            pd.read_excel(uploaded_file, nrows=3)
            if name.endswith(".xlsx")
            else pd.read_csv(uploaded_file, nrows=3, encoding="latin-1")
        )
        if len(test) == 0:
            return False, "File appears empty."
    except (ValueError, pd.errors.ParserError, OSError) as e:
        return False, f"Cannot read file: {e}"
    uploaded_file.seek(0)
    return True, ""


def load_and_process(uploaded=None, use_sample=False) -> bool:
    file_name = "sample_data" if use_sample \
                else getattr(uploaded, "name", "unknown")

    if file_name == st.session_state.last_file_name and \
       st.session_state.df_clean is not None:
        return True

    try:
        with st.spinner("⚡ Processing your data..."):
            if use_sample:
                if not os.path.exists(SAMPLE_PATH):
                    st.error("Sample data not found. Place sales_data.csv in data/ folder.")
                    return False
                df_raw = pd.read_csv(SAMPLE_PATH, encoding="latin-1")
            else:
                uploaded.seek(0)
                df_raw = (
                    pd.read_excel(uploaded)
                    if uploaded.name.lower().endswith(".xlsx")
                    else pd.read_csv(uploaded, encoding="latin-1")
                )

            df_clean, report = clean_dataframe(df_raw.copy())
            ok, missing = validate_dataframe(df_clean)
            if not ok:
                st.error(f"❌ Missing required columns: **{', '.join(missing)}**")
                return False

            findings   = compute_findings(df_clean)
            df_summary = get_df_summary(df_clean)
            save_to_db(df_clean)

            st.session_state.update({
                "df_clean"       : df_clean,
                "findings"       : findings,
                "df_summary"     : df_summary,
                "clean_report"   : report,
                "last_file_name" : file_name,
                "ai_summary"     : None,
                "recommendations": None,
                "qa_history"     : [],
            })
            log.info("Session %s: loaded %d rows from '%s'",
                     st.session_state.session_id, len(df_clean), file_name)
            return True

    except MemoryError:
        st.error("❌ File too large. Try a smaller file.")
        return False
    except (ValueError, pd.errors.ParserError, OSError, RuntimeError) as e:
        log.error("Load error: %s", e)
        st.error(f"❌ Failed to load: {e}")
        return False


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class='sidebar-brand'>
        <span class='sidebar-logo'>📊</span>
        <div class='sidebar-title'>CampaignIQ</div>
        <div class='sidebar-sub'>Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("**📁 Data Source**")
    source = st.radio(
        "source", ["📂 Upload CSV / Excel", "🗂️ Use sample data"],
        index=1, label_visibility="collapsed"
    )

    if source == "📂 Upload CSV / Excel":
        uploaded_file = st.file_uploader(
            "file", type=["csv", "xlsx"],
            label_visibility="collapsed",
            help="Max 50 MB · CSV or Excel"
        )
        if uploaded_file:
            ok, err = validate_upload(uploaded_file)
            if not ok:
                st.error(err)
            else:
                load_and_process(uploaded=uploaded_file)
    else:
        load_and_process(use_sample=True)
        if st.session_state.df_clean is not None:
            st.markdown("<div class='badge badge-success'>✓ Sample data loaded</div>",
                        unsafe_allow_html=True)

    df = st.session_state.df_clean
    if df is not None:
        st.divider()
        findings_data = st.session_state.findings
        margin_val    = findings_data.get("overall_margin_%", 0)

        st.markdown("**📊 Dataset**")
        c1, c2 = st.columns(2)
        c1.metric("Rows",    f"{len(df):,}")
        c2.metric("Columns", len(df.columns))

        if findings_data:
            st.metric("💰 Revenue", f"${findings_data.get('total_revenue',0):,.0f}")
            badge = "badge-success" if margin_val > 15 else "badge-warning" if margin_val > 10 else "badge-danger"
            badge_txt = "✅ Healthy" if margin_val > 15 else "⚠️ Low" if margin_val > 10 else "🔴 Critical"
            st.markdown(
                f"**Margin:** {margin_val:.1f}%  "
                f"<span class='badge {badge}'>{badge_txt}</span>",
                unsafe_allow_html=True
            )

        cr = st.session_state.clean_report
        if cr:
            with st.expander("🔍 Data Quality", expanded=False):
                st.caption(f"Rows before: **{cr.get('rows_before',0):,}**")
                st.caption(f"Rows after:  **{cr.get('rows_after',0):,}**")
                st.caption(f"Duplicates:  **{cr.get('duplicates',0):,}**")
                for col, info in cr.get("outliers", {}).items():
                    st.caption(f"{col} capped: **{info['outliers_capped']:,}**")

    st.divider()
    with st.expander("🔑 AI Settings", expanded=False):
        st.caption("Free keys — no credit card needed")
        gk = st.text_input("Gemini API Key", type="password",
                           placeholder="AIza...",
                           help="aistudio.google.com — 1,500/day free")
        if gk:
            st.session_state["GEMINI_API_KEY"] = gk
            st.markdown("<div class='badge badge-success'>✓ Gemini active</div>",
                        unsafe_allow_html=True)
        qk = st.text_input("Groq API Key", type="password",
                           placeholder="gsk_...",
                           help="console.groq.com — 100/day free")
        if qk:
            st.session_state["GROQ_API_KEY"] = qk
            st.markdown("<div class='badge badge-success'>✓ Groq active</div>",
                        unsafe_allow_html=True)

    st.divider()
    st.markdown("**🗺 Navigation**")
    st.page_link("app.py",                          label="🏠 Home")
    st.page_link("pages/01_dashboard.py",           label="📊 Dashboard")
    st.page_link("pages/02_ai_insights.py",         label="🤖 AI Insights")
    st.page_link("pages/03_recommendations.py",     label="💡 Recommendations")
    st.page_link("pages/04_export.py",              label="📥 Export")

# ── Main ──────────────────────────────────────────────────────
if st.session_state.df_clean is None:
    # ── Hero ──
    st.markdown("""
    <div style='padding:60px 0 40px'>
        <p class='hero-title'>Campaign<br>Intelligence.</p>
        <p class='hero-sub'>Upload your sales data — get instant, AI-powered campaign insights.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc in [
        (c1, "⚡", "Instant Results",  "CSV → insights in seconds"),
        (c2, "📊", "8 Live Charts",    "Interactive & filterable"),
        (c3, "🤖", "AI Analysis",      "Plain-English summaries"),
        (c4, "📥", "Excel Export",     "7-sheet detailed report"),
    ]:
        col.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-icon'>{icon}</div>
            <div class='kpi-value'>{title}</div>
            <div class='kpi-label'>{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Select **Use sample data** in the sidebar to explore instantly.")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:24px'>
            <div style='font-family:Syne,sans-serif;font-size:15px;font-weight:700;color:#E2E8F0;margin-bottom:14px'>
                ✦ Works with any sales CSV
            </div>
            <div class='feature-grid'>
                <div class='feature-item'><strong>Shopify</strong>Order exports</div>
                <div class='feature-item'><strong>WooCommerce</strong>Sales reports</div>
                <div class='feature-item'><strong>Salesforce</strong>CRM exports</div>
                <div class='feature-item'><strong>QuickBooks</strong>Financial data</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with col_r:
        st.markdown("**Minimum required columns:**")
        st.dataframe(pd.DataFrame({
            "Column"  : ["Sales", "Profit", "Discount", "Region", "Segment"],
            "Example" : ["261.96", "41.91", "0.2", "West", "Consumer"],
            "Required": ["✅", "✅", "✅", "Optional", "Optional"],
        }), hide_index=True, use_container_width=True)

else:
    df       = st.session_state.df_clean
    findings = st.session_state.findings
    summary  = st.session_state.get("df_summary", {})
    margin   = findings.get("overall_margin_%", 0)
    lift     = findings.get("campaign_lift_%", 0)
    date_r   = summary.get("date_range", "N/A")

    # ── Welcome header ──
    st.markdown(f"""
    <div style='padding:24px 0 8px'>
        <p style='font-family:Syne,sans-serif;font-size:28px;font-weight:800;
                  color:#F1F5F9;margin:0;letter-spacing:-0.02em'>👋 Welcome back</p>
        <div class='stat-strip'>
            <span class='stat-chip'>📁 {st.session_state.last_file_name}</span>
            <span class='stat-chip'>📋 {len(df):,} records</span>
            <span class='stat-chip'>📅 {date_r}</span>
            <span class='stat-chip'>🔑 Session {st.session_state.session_id}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── KPI strip ──
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("💰 Revenue",       f"${findings.get('total_revenue',0):,.0f}")
    k2.metric("📈 Profit",        f"${findings.get('total_profit',0):,.0f}")
    k3.metric("📊 Margin",        f"{margin:.1f}%")
    k4.metric("🎯 Campaign %",    f"{findings.get('campaign_orders_%',0):.0f}%")
    k5.metric("📦 Campaign Lift", f"{lift:+.1f}%")
    st.divider()

    # ── Alerts ──
    if margin < 10:
        st.markdown(f"<div class='alert-critical'>🔴 <strong>Critical:</strong> Margin is only {margin:.1f}% — visit Recommendations immediately.</div>", unsafe_allow_html=True)
    elif margin < 15:
        st.markdown(f"<div class='alert-warning'>🟡 <strong>Watch:</strong> Margin {margin:.1f}% is below the 15% benchmark.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='alert-success'>🟢 <strong>Healthy:</strong> Margin {margin:.1f}% is above benchmark.</div>", unsafe_allow_html=True)

    if lift < 0:
        st.markdown(f"<div class='alert-warning'>⚠️ Campaign lift is {lift:.1f}% — discounts may be hurting profitability.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Nav cards using st.page_link ──
    st.markdown("<p style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#4B5563;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px'>Explore</p>", unsafe_allow_html=True)

    n1, n2, n3, n4 = st.columns(4)

    with n1:
        st.page_link("pages/01_dashboard.py", label="📊 Dashboard", use_container_width=True)
        st.caption("8 interactive charts")

    with n2:
        st.page_link("pages/02_ai_insights.py", label="🤖 AI Insights", use_container_width=True)
        st.caption("AI analysis + Q&A")

    with n3:
        st.page_link("pages/03_recommendations.py", label="💡 Recommendations", use_container_width=True)
        st.caption("6 ranked actions")

    with n4:
        st.page_link("pages/04_export.py", label="📥 Export", use_container_width=True)
        st.caption("Excel + CSV download")
