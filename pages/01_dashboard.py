# ============================================================
# pages/01_dashboard.py — Interactive Campaign Dashboard
# Premium UI with glassmorphism & animated charts
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

if "df_clean" not in st.session_state or st.session_state.df_clean is None:
    st.warning("⚠️ No data loaded. Go to the Home page first.")
    st.page_link("app.py", label="← Go Home")
    st.stop()

df = st.session_state.df_clean
findings = st.session_state.get("findings", {})

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
.stApp { background:#050810; font-family:'DM Sans',sans-serif; }
.stApp::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
    background:
        radial-gradient(ellipse 80% 60% at 20% 10%, rgba(99,102,241,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 80% at 80% 80%, rgba(16,185,129,0.08) 0%, transparent 60%);
}
h1,h2,h3 { font-family:'Syne',sans-serif !important; letter-spacing:-0.02em; }
#MainMenu,footer,header { visibility:hidden; }
[data-testid="stSidebar"] { background:rgba(10,12,24,0.95)!important; border-right:1px solid rgba(99,102,241,0.2)!important; }
[data-testid="stMetric"] { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:12px; padding:16px!important; }
[data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; font-size:22px!important; color:#F1F5F9!important; }
[data-testid="stMetricLabel"] { color:#64748B!important; font-size:12px!important; }
.section-title { font-family:'Syne',sans-serif; font-size:13px; font-weight:700; color:#4B5563; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px; }
.filter-chip { display:inline-block; background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2); border-radius:20px; padding:3px 10px; font-size:11px; color:#A5B4FC; margin:2px; }
hr { border:none!important; border-top:1px solid rgba(255,255,255,0.06)!important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Chart theme ───────────────────────────────────────────────
C = {
    "indigo": "#6366F1",
    "emerald": "#10B981",
    "amber": "#F59E0B",
    "rose": "#F43F5E",
    "violet": "#8B5CF6",
    "teal": "#0D9488",
    "sky": "#0EA5E9",
    "lime": "#84CC16",
}
PALETTE = list(C.values())
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="DM Sans, sans-serif", size=12),
    margin=dict(l=10, r=10, t=36, b=10),
)

# ── Sidebar filters ───────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='section-title'>Filters</div>", unsafe_allow_html=True)
    regions = sorted(df["Region"].dropna().unique()) if "Region" in df.columns else []
    segments = (
        sorted(df["Segment"].dropna().unique()) if "Segment" in df.columns else []
    )
    categories = (
        sorted(df["Category"].dropna().unique()) if "Category" in df.columns else []
    )

    sel_regions = st.multiselect("Region", regions, default=regions)
    sel_segments = st.multiselect("Segment", segments, default=segments)
    sel_categories = st.multiselect("Category", categories, default=categories)

    date_filter = None
    if (
        "Order_Date" in df.columns
        and pd.api.types.is_datetime64_any_dtype(df["Order_Date"])
        and df["Order_Date"].notna().any()
    ):
        min_d = df["Order_Date"].min().date()
        max_d = df["Order_Date"].max().date()
        date_filter = st.date_input(
            "Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d
        )
    if st.button("↺ Reset Filters", use_container_width=True):
        st.rerun()

# ── Apply filters ─────────────────────────────────────────────
mask = pd.Series(True, index=df.index)
if sel_regions and "Region" in df.columns:
    mask &= df["Region"].isin(sel_regions)
if sel_segments and "Segment" in df.columns:
    mask &= df["Segment"].isin(sel_segments)
if sel_categories and "Category" in df.columns:
    mask &= df["Category"].isin(sel_categories)
if (
    date_filter
    and len(date_filter) == 2
    and "Order_Date" in df.columns
    and pd.api.types.is_datetime64_any_dtype(df["Order_Date"])
):
    mask &= (df["Order_Date"].dt.date >= date_filter[0]) & (
        df["Order_Date"].dt.date <= date_filter[1]
    )

fdf = df[mask].copy()
if fdf.empty:
    st.error("No data matches selected filters.")
    st.stop()

# ── Header ────────────────────────────────────────────────────
total_sales = fdf["Sales"].sum()
total_profit = fdf["Profit"].sum()
total_orders = fdf["Order_ID"].nunique() if "Order_ID" in fdf.columns else len(fdf)
overall_margin = (total_profit / total_sales * 100) if total_sales else 0

if "Is_Campaign_Order" in fdf.columns:
    camp_mask = fdf["Is_Campaign_Order"].astype(bool)
    camp_avg = fdf.loc[camp_mask, "Sales"].mean() if camp_mask.sum() > 0 else 0.0
    no_camp_avg = fdf.loc[~camp_mask, "Sales"].mean() if (~camp_mask).sum() > 0 else 0.0
else:
    camp_avg = no_camp_avg = 0.0
lift = ((camp_avg - no_camp_avg) / no_camp_avg * 100) if no_camp_avg else 0

st.markdown(
    f"""
<div style='padding:20px 0 8px'>
    <p style='font-family:Syne,sans-serif;font-size:26px;font-weight:800;color:#F1F5F9;margin:0;letter-spacing:-0.02em'>
        📊 Dashboard
    </p>
    <p style='color:#4B5563;font-size:13px;margin:6px 0 0'>
        {len(fdf):,} of {len(df):,} records &nbsp;·&nbsp;
        {len(sel_regions)} regions &nbsp;·&nbsp; {len(sel_segments)} segments
    </p>
</div>
""",
    unsafe_allow_html=True,
)
st.divider()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Revenue", f"${total_sales:,.0f}")
k2.metric("📈 Profit", f"${total_profit:,.0f}")
k3.metric(
    "📊 Margin",
    f"{overall_margin:.1f}%",
    delta="Healthy ✅" if overall_margin > 15 else "Low ⚠️",
)
k4.metric("🎯 Orders", f"{total_orders:,}")
k5.metric("📦 Campaign Lift", f"{lift:+.1f}%", delta="vs non-campaign")
st.divider()

# ── Row 1: Trend + Region ─────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown(
        "<div class='section-title'>Monthly Revenue & Profit</div>",
        unsafe_allow_html=True,
    )
    if (
        "Order_Date" in fdf.columns
        and pd.api.types.is_datetime64_any_dtype(fdf["Order_Date"])
        and fdf["Order_Date"].notna().any()
    ):
        dates = fdf["Order_Date"]
        if hasattr(dates.dt, "tz") and dates.dt.tz is not None:
            dates = dates.dt.tz_localize(None)
        monthly = (
            fdf.assign(_period=dates.dt.to_period("M"))
            .groupby("_period")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
        )
        monthly["Month"] = monthly["_period"].dt.to_timestamp()
        monthly = monthly.sort_values("Month")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=monthly["Month"],
                y=monthly["Sales"],
                name="Revenue",
                mode="lines+markers",
                line=dict(color=C["indigo"], width=2.5),
                fill="tozeroy",
                fillcolor="rgba(99,102,241,0.07)",
                marker=dict(
                    size=5, color=C["indigo"], line=dict(color="#050810", width=2)
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=monthly["Month"],
                y=monthly["Profit"],
                name="Profit",
                mode="lines",
                line=dict(color=C["emerald"], width=2, dash="dot"),
            )
        )
        fig.update_layout(
            **LAYOUT, hovermode="x unified", legend=dict(orientation="h", y=1.12, x=0)
        )
        fig.update_yaxes(
            tickprefix="$",
            tickformat=",.0f",
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
        )
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.03)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Date column not available.")

with col2:
    st.markdown(
        "<div class='section-title'>Revenue by Region</div>", unsafe_allow_html=True
    )
    if "Region" in fdf.columns:
        reg = (
            fdf.groupby("Region")
            .agg(Sales=("Sales", "sum"), Margin=("Profit_Margin_", "mean"))
            .reset_index()
            .sort_values("Sales", ascending=True)
        )
        fig2 = go.Figure(
            go.Bar(
                x=reg["Sales"],
                y=reg["Region"],
                orientation="h",
                marker=dict(
                    color=reg["Sales"],
                    colorscale=[
                        [0, "rgba(99,102,241,0.3)"],
                        [1, "rgba(99,102,241,0.9)"],
                    ],
                    showscale=False,
                ),
                text=reg["Sales"].apply(lambda x: f"${x:,.0f}"),
                textposition="outside",
                textfont=dict(color="#94A3B8", size=11),
            )
        )
        fig2.update_layout(
            **LAYOUT,
            showlegend=False,
            xaxis=dict(
                tickprefix="$", tickformat=",.0f", gridcolor="rgba(255,255,255,0.04)"
            ),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Segment + Treemap ──────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown(
        "<div class='section-title'>Segment Performance</div>", unsafe_allow_html=True
    )
    if "Segment" in fdf.columns:
        seg = (
            fdf.groupby("Segment")
            .agg(
                Sales=("Sales", "sum"),
                Profit=("Profit", "sum"),
                Margin=("Profit_Margin_", "mean"),
            )
            .reset_index()
            .sort_values("Sales", ascending=False)
        )
        fig3 = make_subplots(1, 2, specs=[[{"type": "pie"}, {"type": "bar"}]])
        fig3.add_trace(
            go.Pie(
                labels=seg["Segment"],
                values=seg["Sales"],
                hole=0.6,
                marker_colors=PALETTE,
                textinfo="label+percent",
                textfont=dict(size=11),
            ),
            1,
            1,
        )
        fig3.add_trace(
            go.Bar(
                x=seg["Segment"],
                y=seg["Margin"],
                marker_color=PALETTE,
                text=seg["Margin"].apply(lambda x: f"{x:.1f}%"),
                textposition="outside",
            ),
            1,
            2,
        )
        fig3.update_layout(
            **LAYOUT,
            showlegend=False,
            height=260,
            yaxis2=dict(gridcolor="rgba(255,255,255,0.04)"),
        )
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown(
        "<div class='section-title'>Category Profit Treemap</div>",
        unsafe_allow_html=True,
    )
    if "Category" in fdf.columns:
        cat = (
            fdf.groupby("Category")
            .agg(Sales=("Sales", "sum"), Margin=("Profit_Margin_", "mean"))
            .reset_index()
        )
        margin_min = cat["Margin"].min()
        margin_max = cat["Margin"].max()
        if margin_max - margin_min < 0.01:
            fig4 = px.treemap(
                cat, path=["Category"], values="Sales", color_discrete_sequence=PALETTE
            )
        else:
            fig4 = px.treemap(
                cat,
                path=["Category"],
                values="Sales",
                color="Margin",
                color_continuous_scale=["#4C0519", "#7C3AED", "#064E3B"],
                color_continuous_midpoint=cat["Margin"].mean(),
            )
        fig4.update_layout(**LAYOUT, height=260)
        fig4.update_traces(
            texttemplate="<b>%{label}</b><br>$%{value:,.0f}", textfont_size=12
        )
        st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Campaign + Discount ROI ───────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.markdown(
        "<div class='section-title'>Campaign vs Non-Campaign</div>",
        unsafe_allow_html=True,
    )
    if "Is_Campaign_Order" in fdf.columns:
        cmp = (
            fdf.groupby("Is_Campaign_Order")
            .agg(
                Avg_Sales=("Sales", "mean"),
                Avg_Profit=("Profit", "mean"),
                Avg_Margin=("Profit_Margin_", "mean"),
            )
            .reset_index()
        )
        cmp["Type"] = cmp["Is_Campaign_Order"].map(
            {True: "Campaign", False: "No Campaign", 1: "Campaign", 0: "No Campaign"}
        )
        fig5 = go.Figure()
        for metric, label, color in [
            ("Avg_Sales", "Avg Sales", C["indigo"]),
            ("Avg_Profit", "Avg Profit", C["emerald"]),
            ("Avg_Margin", "Avg Margin", C["amber"]),
        ]:
            fig5.add_trace(
                go.Bar(
                    name=label,
                    x=cmp["Type"],
                    y=cmp[metric],
                    marker_color=color,
                    opacity=0.85,
                    text=cmp[metric].apply(
                        lambda x, lbl=label: (
                            f"${x:.0f}"
                            if "Sales" in lbl or "Profit" in lbl
                            else f"{x:.1f}%"
                        )
                    ),
                    textposition="outside",
                )
            )
        fig5.update_layout(
            **LAYOUT,
            barmode="group",
            legend=dict(orientation="h", y=1.12),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        )
        st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown(
        "<div class='section-title'>Discount Band ROI</div>", unsafe_allow_html=True
    )
    if "Discount_Band" in fdf.columns:
        disc = (
            fdf.groupby("Discount_Band", observed=True)
            .agg(Avg_Margin=("Profit_Margin_", "mean"), Orders=("Sales", "count"))
            .reset_index()
            .dropna(subset=["Discount_Band"])
        )
        disc = disc[disc["Discount_Band"].astype(str) != "nan"]
        colors_d = [
            C["emerald"] if m > 15 else C["amber"] if m > 0 else C["rose"]
            for m in disc["Avg_Margin"]
        ]
        fig6 = go.Figure(
            go.Bar(
                x=disc["Discount_Band"].astype(str),
                y=disc["Avg_Margin"],
                marker_color=colors_d,
                opacity=0.85,
                text=disc["Avg_Margin"].apply(lambda x: f"{x:.1f}%"),
                textposition="outside",
            )
        )
        fig6.add_hline(
            y=0,
            line_dash="dash",
            line_color=C["rose"],
            annotation_text="Break-even",
            annotation_position="right",
            annotation_font_color="#F43F5E",
        )
        fig6.update_layout(
            **LAYOUT, showlegend=False, yaxis=dict(gridcolor="rgba(255,255,255,0.04)")
        )
        st.plotly_chart(fig6, use_container_width=True)

# ── Row 4: Top Products + Heatmap ────────────────────────────
col7, col8 = st.columns(2)

with col7:
    st.markdown(
        "<div class='section-title'>Top 10 Sub-Categories</div>", unsafe_allow_html=True
    )
    if "Sub_Category" in fdf.columns:
        sub = (
            fdf.groupby("Sub_Category")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
            .nlargest(10, "Sales")
            .sort_values("Sales", ascending=True)
        )
        bar_colors = [C["emerald"] if p > 0 else C["rose"] for p in sub["Profit"]]
        fig7 = go.Figure(
            go.Bar(
                x=sub["Sales"],
                y=sub["Sub_Category"],
                orientation="h",
                marker_color=bar_colors,
                opacity=0.85,
                text=sub["Sales"].apply(lambda x: f"${x:,.0f}"),
                textposition="outside",
            )
        )
        fig7.update_layout(
            **LAYOUT,
            showlegend=False,
            xaxis=dict(
                tickprefix="$", tickformat=",.0f", gridcolor="rgba(255,255,255,0.04)"
            ),
        )
        st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.markdown(
        "<div class='section-title'>Margin Heatmap — Region × Category</div>",
        unsafe_allow_html=True,
    )
    if "Region" in fdf.columns and "Category" in fdf.columns:
        heat = (
            fdf.groupby(["Region", "Category"])["Profit_Margin_"]
            .mean()
            .reset_index()
            .pivot(index="Region", columns="Category", values="Profit_Margin_")
            .round(1)
        )
        fig8 = go.Figure(
            go.Heatmap(
                z=heat.values,
                x=heat.columns.tolist(),
                y=heat.index.tolist(),
                colorscale=[[0, "#4C0519"], [0.5, "#7C3AED"], [1, "#064E3B"]],
                text=[[f"{v:.1f}%" for v in row] for row in heat.values],
                texttemplate="%{text}",
                hovertemplate="Region: %{y}<br>Category: %{x}<br>Margin: %{z:.1f}%<extra></extra>",
            )
        )
        fig8.update_layout(**LAYOUT, height=280)
        st.plotly_chart(fig8, use_container_width=True)

# ── YoY Trend (new!) ──────────────────────────────────────────
if "Order_Year" in fdf.columns and fdf["Order_Year"].notna().any():
    st.divider()
    st.markdown(
        "<div class='section-title'>Year-over-Year Performance</div>",
        unsafe_allow_html=True,
    )
    yoy = (
        fdf.groupby("Order_Year")
        .agg(
            Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Sales", "count")
        )
        .reset_index()
    )
    fig9 = make_subplots(specs=[[{"secondary_y": True}]])
    fig9.add_trace(
        go.Bar(
            x=yoy["Order_Year"],
            y=yoy["Sales"],
            name="Revenue",
            marker_color=C["indigo"],
            opacity=0.8,
        ),
        secondary_y=False,
    )
    fig9.add_trace(
        go.Scatter(
            x=yoy["Order_Year"],
            y=yoy["Orders"],
            name="Orders",
            mode="lines+markers",
            line=dict(color=C["amber"], width=2),
            marker=dict(size=7, color=C["amber"]),
        ),
        secondary_y=True,
    )
    fig9.update_layout(**LAYOUT, barmode="group", legend=dict(orientation="h", y=1.12))
    fig9.update_yaxes(
        tickprefix="$",
        tickformat=",.0f",
        gridcolor="rgba(255,255,255,0.04)",
        secondary_y=False,
    )
    fig9.update_yaxes(title_text="Orders", secondary_y=True)
    st.plotly_chart(fig9, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────
st.divider()
with st.expander("📋 Raw Data Table", expanded=False):
    show = [
        c
        for c in [
            "Order_ID",
            "Order_Date",
            "Region",
            "Segment",
            "Category",
            "Sub_Category",
            "Sales",
            "Profit",
            "Discount",
            "Profit_Margin_",
            "Is_Campaign_Order",
            "Discount_Band",
        ]
        if c in fdf.columns
    ]
    st.dataframe(fdf[show].head(1000), use_container_width=True, hide_index=True)
    st.caption(f"Showing first 1,000 of {len(fdf):,} records")
