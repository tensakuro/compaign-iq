# ============================================================
# pages/04_export.py — Export to Excel and CSV
# Premium UI with progress indicators and preview
# ============================================================

import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime

if "df_clean" not in st.session_state or st.session_state.df_clean is None:
    st.warning("⚠️ No data loaded. Go to the Home page first.")
    st.page_link("app.py", label="← Go Home")
    st.stop()

df       = st.session_state.df_clean
findings = st.session_state.get("findings", {})
now      = datetime.now().strftime("%Y-%m-%d")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
.stApp { background:#050810; font-family:'DM Sans',sans-serif; }
.stApp::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
    background:
        radial-gradient(ellipse 70% 50% at 10% 20%, rgba(99,102,241,0.10) 0%, transparent 60%),
        radial-gradient(ellipse 50% 60% at 90% 80%, rgba(16,185,129,0.07) 0%, transparent 60%);
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
    color:#4B5563; letter-spacing:2px; text-transform:uppercase; margin-bottom:14px;
}

/* Export card */
.export-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 28px;
    height: 100%;
    transition: border-color 0.3s;
}
.export-card:hover { border-color: rgba(99,102,241,0.3); }
.export-card-title {
    font-family: 'Syne', sans-serif;
    font-size: 17px; font-weight: 800;
    color: #F1F5F9; margin-bottom: 6px;
}
.export-card-sub { font-size: 12px; color: #4B5563; margin-bottom: 20px; }

/* Sheet chip */
.sheet-list { display:flex; flex-wrap:wrap; gap:6px; margin:16px 0; }
.sheet-chip {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    color: #A5B4FC;
    font-weight: 500;
}

/* Download row */
.dl-row {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    transition: border-color 0.2s;
}
.dl-row:hover { border-color: rgba(99,102,241,0.25); }
.dl-icon  { font-size: 20px; }
.dl-info  { flex: 1; }
.dl-name  { font-size: 13px; font-weight: 600; color: #E2E8F0; }
.dl-desc  { font-size: 11px; color: #4B5563; margin-top: 2px; }

/* Preview table */
.preview-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin: 16px 0;
}
.preview-cell {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 14px 18px;
}
.preview-cell-label { font-size: 11px; color: #4B5563; text-transform: uppercase; letter-spacing: 1px; }
.preview-cell-value { font-family:'Syne',sans-serif; font-size:18px; font-weight:700; color:#F1F5F9; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

MAX_EXPORT = 10_000

# ── Header ────────────────────────────────────────────────────
st.markdown(f"""
<div style='padding:20px 0 8px'>
    <p style='font-family:Syne,sans-serif;font-size:26px;font-weight:800;
              color:#F1F5F9;margin:0;letter-spacing:-0.02em'>📥 Export</p>
    <p style='color:#4B5563;font-size:13px;margin:6px 0 0'>
        {len(df):,} records &nbsp;·&nbsp; Report date: {now}
    </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Preview strip ─────────────────────────────────────────────
p1, p2, p3, p4 = st.columns(4)
p1.metric("💰 Revenue",  f"${findings.get('total_revenue',0):,.0f}")
p2.metric("📈 Profit",   f"${findings.get('total_profit',0):,.0f}")
p3.metric("📊 Margin",   f"{findings.get('overall_margin_%',0):.1f}%")
p4.metric("📋 Records",  f"{len(df):,}")
st.divider()

col1, col2 = st.columns([3, 2])

# ── Excel Export ──────────────────────────────────────────────
with col1:
    st.markdown("""
    <div class='export-card'>
        <div class='export-card-title'>📊 Full Excel Report</div>
        <div class='export-card-sub'>7 sheets · Complete analysis package</div>
        <div class='sheet-list'>
            <span class='sheet-chip'>📋 Summary</span>
            <span class='sheet-chip'>🗺️ Regional</span>
            <span class='sheet-chip'>👥 Segments</span>
            <span class='sheet-chip'>📦 Categories</span>
            <span class='sheet-chip'>💸 Discounts</span>
            <span class='sheet-chip'>📈 Monthly</span>
            <span class='sheet-chip'>🗄️ Raw Data</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("⚡ Build Excel Report", type="primary", use_container_width=True):
        with st.spinner("Building your report..."):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:

                # Sheet 1: Summary
                pd.DataFrame({
                    "Metric": [
                        "Total Revenue","Total Profit","Margin %",
                        "Campaign Orders %","Campaign Lift %",
                        "Best Region","Best Segment","Best Category",
                        "Peak Month","Best Discount Band","Records","Date",
                    ],
                    "Value": [
                        f"${findings.get('total_revenue',0):,.2f}",
                        f"${findings.get('total_profit',0):,.2f}",
                        f"{findings.get('overall_margin_%',0):.1f}%",
                        f"{findings.get('campaign_orders_%',0):.1f}%",
                        f"{findings.get('campaign_lift_%',0):+.1f}%",
                        findings.get("best_region","N/A"),
                        findings.get("best_segment","N/A"),
                        findings.get("best_category","N/A"),
                        findings.get("peak_month","N/A"),
                        findings.get("best_discount_band","N/A"),
                        f"{len(df):,}", now,
                    ]
                }).to_excel(writer, sheet_name="Summary", index=False)

                # Sheet 2: Regional
                if "Region" in df.columns:
                    (df.groupby("Region")
                       .agg(Revenue=("Sales","sum"), Profit=("Profit","sum"),
                            Margin=("Profit_Margin_","mean"), Orders=("Sales","count"))
                       .round(2).reset_index()
                    ).to_excel(writer, sheet_name="Regional", index=False)

                # Sheet 3: Segments
                if "Segment" in df.columns:
                    (df.groupby("Segment")
                       .agg(Revenue=("Sales","sum"), Profit=("Profit","sum"),
                            Margin=("Profit_Margin_","mean"), Avg_Order=("Sales","mean"))
                       .round(2).reset_index()
                    ).to_excel(writer, sheet_name="Segments", index=False)

                # Sheet 4: Categories
                if "Category" in df.columns:
                    (df.groupby("Category")
                       .agg(Revenue=("Sales","sum"), Profit=("Profit","sum"),
                            Margin=("Profit_Margin_","mean"))
                       .round(2).reset_index()
                    ).to_excel(writer, sheet_name="Categories", index=False)

                # Sheet 5: Discount Analysis
                if "Discount_Band" in df.columns:
                    disc = (
                        df.groupby("Discount_Band", observed=True)
                          .agg(Orders=("Sales","count"), Avg_Sales=("Sales","mean"),
                               Avg_Profit=("Profit","mean"), Avg_Margin=("Profit_Margin_","mean"),
                               Total_Revenue=("Sales","sum"), Total_Profit=("Profit","sum"))
                          .round(2).reset_index()
                    )
                    disc = disc[disc["Discount_Band"].astype(str) != "nan"]
                    disc.to_excel(writer, sheet_name="Discount Analysis", index=False)

                # Sheet 6: Monthly Trend
                if "Order_Date" in df.columns and \
                   pd.api.types.is_datetime64_any_dtype(df["Order_Date"]):
                    (df.groupby([
                        df["Order_Date"].dt.year.rename("Year"),
                        df["Order_Date"].dt.month.rename("Month"),
                    ]).agg(Sales=("Sales","sum"), Profit=("Profit","sum"), Orders=("Sales","count"))
                     .round(2).reset_index()
                    ).to_excel(writer, sheet_name="Monthly Trend", index=False)

                # Sheet 7: Raw Data
                total_rows  = len(df)
                export_rows = min(total_rows, MAX_EXPORT)
                export_cols = [c for c in [
                    "Order_ID","Order_Date","Region","Segment","Category",
                    "Sub_Category","Sales","Profit","Discount","Profit_Margin_",
                    "Is_Campaign_Order","Discount_Band","Delivery_Days",
                ] if c in df.columns]
                df[export_cols].head(export_rows).to_excel(
                    writer, sheet_name="Raw Data", index=False)
                if total_rows > export_rows:
                    st.info(f"ℹ️ Raw Data: first {export_rows:,} of {total_rows:,} rows")

            buf.seek(0)
            st.download_button(
                label="⬇️ Download Excel Report",
                data=buf,
                file_name=f"campaigniq_report_{now}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.success("✅ Excel report ready — 7 sheets")

# ── CSV Downloads ─────────────────────────────────────────────
with col2:
    st.markdown("<div class='section-title'>Quick Downloads</div>", unsafe_allow_html=True)

    downloads = []

    downloads.append(("📄", "Cleaned Sales Data", "Full cleaned dataset as CSV",
        df.to_csv(index=False).encode("utf-8"),
        f"sales_clean_{now}.csv", "text/csv"))

    downloads.append(("🔬", "Key Findings (JSON)", "All computed metrics",
        json.dumps(findings, indent=2).encode("utf-8"),
        f"findings_{now}.json", "application/json"))

    if "Region" in df.columns:
        reg_csv = (
            df.groupby("Region")
              .agg(Revenue=("Sales","sum"), Profit=("Profit","sum"),
                   Margin=("Profit_Margin_","mean"), Orders=("Sales","count"))
              .round(2).reset_index()
              .to_csv(index=False).encode("utf-8")
        )
        downloads.append(("🗺️", "Regional Summary", "Revenue by region",
            reg_csv, f"regional_{now}.csv", "text/csv"))

    if "Segment" in df.columns:
        seg_csv = (
            df.groupby("Segment")
              .agg(Revenue=("Sales","sum"), Profit=("Profit","sum"),
                   Margin=("Profit_Margin_","mean"))
              .round(2).reset_index()
              .to_csv(index=False).encode("utf-8")
        )
        downloads.append(("👥", "Segment Summary", "Revenue by segment",
            seg_csv, f"segment_{now}.csv", "text/csv"))

    if "Discount_Band" in df.columns:
        disc_csv = (
            df.groupby("Discount_Band", observed=True)
              .agg(Orders=("Sales","count"), Avg_Margin=("Profit_Margin_","mean"),
                   Total_Profit=("Profit","sum"))
              .round(2).reset_index()
              .to_csv(index=False).encode("utf-8")
        )
        downloads.append(("💸", "Discount ROI", "Discount band analysis",
            disc_csv, f"discount_roi_{now}.csv", "text/csv"))

    for icon, name, desc, data, fname, mime in downloads:
        st.markdown(f"""
        <div class='dl-row'>
            <div class='dl-icon'>{icon}</div>
            <div class='dl-info'>
                <div class='dl-name'>{name}</div>
                <div class='dl-desc'>{desc}</div>
            </div>
        </div>""", unsafe_allow_html=True)
        st.download_button(
            f"⬇️ {name}",
            data=data, file_name=fname, mime=mime,
            use_container_width=True, key=f"dl_{fname}"
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

st.divider()

# ── Data preview ──────────────────────────────────────────────
with st.expander("📋 Data Preview", expanded=False):
    show = [c for c in [
        "Order_ID","Order_Date","Region","Segment","Category","Sub_Category",
        "Sales","Profit","Discount","Profit_Margin_","Is_Campaign_Order","Discount_Band"
    ] if c in df.columns]
    st.dataframe(df[show].head(500), use_container_width=True, hide_index=True)
    st.caption(f"Showing 500 of {len(df):,} records · File: {st.session_state.get('last_file_name','N/A')}")
