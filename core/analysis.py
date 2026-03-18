# ============================================================
# core/analysis.py — Analytics computation layer
# ============================================================

import pandas as pd
import math
import logging

log = logging.getLogger(__name__)

MONTH_NAMES = {
    1:"Jan", 2:"Feb",  3:"Mar", 4:"Apr",
    5:"May", 6:"Jun",  7:"Jul", 8:"Aug",
    9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec",
}


def safe_float(val, default: float = 0.0) -> float:
    try:
        result = float(val)
        return default if math.isnan(result) else result
    except (TypeError, ValueError, OverflowError):
        return default


def compute_findings(df: pd.DataFrame) -> dict:
    """Compute all key findings. Returns plain-Python dict."""
    if df is None or df.empty:
        return {}

    findings     = {}
    total_sales  = safe_float(df["Sales"].sum())
    total_profit = safe_float(df["Profit"].sum())
    total_rows   = len(df)

    # Overall
    findings["total_revenue"]    = round(total_sales, 2)
    findings["total_profit"]     = round(total_profit, 2)
    findings["total_records"]    = total_rows
    findings["overall_margin_%"] = round(
        (total_profit / total_sales * 100) if total_sales != 0 else 0.0, 1
    )

    # Campaign
    if "Is_Campaign_Order" in df.columns:
        camp_mask = df["Is_Campaign_Order"].astype(bool)
        camp_n    = int(camp_mask.sum())
        findings["campaign_orders"]   = camp_n
        findings["campaign_orders_%"] = round(
            camp_n / total_rows * 100 if total_rows > 0 else 0.0, 1
        )
        camp_avg    = safe_float(df[camp_mask]["Sales"].mean())
        nocamp_avg  = safe_float(df[~camp_mask]["Sales"].mean())
        findings["campaign_avg_order"]    = round(camp_avg, 2)
        findings["no_campaign_avg_order"] = round(nocamp_avg, 2)
        findings["campaign_lift_%"]       = round(
            (camp_avg - nocamp_avg) / nocamp_avg * 100
            if nocamp_avg != 0 else 0.0, 1
        )
        findings["campaign_avg_margin"]    = round(
            safe_float(df[camp_mask]["Profit_Margin_"].mean()), 1
        )
        findings["no_campaign_avg_margin"] = round(
            safe_float(df[~camp_mask]["Profit_Margin_"].mean()), 1
        )

    # Region
    if "Region" in df.columns:
        r = df.groupby("Region")["Sales"].sum()
        findings["best_region"]  = str(r.idxmax())
        findings["worst_region"] = str(r.idxmin())
        findings["region_count"] = int(df["Region"].nunique())

    # Segment
    if "Segment" in df.columns:
        s = df.groupby("Segment")["Sales"].sum()
        findings["best_segment"] = str(s.idxmax())

    # Category
    if "Category" in df.columns:
        c = df.groupby("Category")["Profit"].sum()
        findings["best_category"]  = str(c.idxmax())
        findings["worst_category"] = str(c.idxmin())

    # Sub-category
    if "Sub_Category" in df.columns:
        sc = df.groupby("Sub_Category")["Sales"].sum()
        findings["best_subcategory"] = str(sc.idxmax())

    # Seasonality
    if "Order_Month" in df.columns and \
       not df["Order_Month"].isna().all():
        monthly = df.groupby("Order_Month")["Sales"].mean()
        peak_m  = monthly.idxmax()
        low_m   = monthly.idxmin()
        findings["peak_month"]   = MONTH_NAMES.get(int(peak_m), str(peak_m))
        findings["low_month"]    = MONTH_NAMES.get(int(low_m),  str(low_m))
        findings["peak_month_n"] = int(peak_m)

    # YoY
    if "Order_Year" in df.columns and \
       not df["Order_Year"].isna().all():
        yearly = df.groupby("Order_Year")["Sales"].sum().astype(float)
        if len(yearly) >= 2:
            yoy = safe_float(yearly.pct_change().iloc[-1] * 100)
            findings["yoy_growth_%"] = round(yoy, 1)
        findings["best_year"]  = int(yearly.idxmax())
        findings["year_count"] = len(yearly)

    # Discount
    if "Discount_Band" in df.columns:
        bd = df.groupby("Discount_Band", observed=True).agg(
            profit=("Profit","sum"), margin=("Profit_Margin_","mean")
        )
        valid = bd[bd["profit"] > 0]
        if not valid.empty:
            findings["best_discount_band"] = str(valid["margin"].idxmax())
        worst = bd[bd["profit"] < 0]
        if not worst.empty:
            findings["worst_discount_band"] = str(worst["profit"].idxmin())

    # Delivery
    if "Delivery_Days" in df.columns:
        findings["avg_delivery_days"] = round(
            safe_float(df["Delivery_Days"].mean()), 1
        )

    return findings


def get_df_summary(df: pd.DataFrame) -> dict:
    return {
        "records"   : len(df),
        "revenue"   : safe_float(df["Sales"].sum()),
        "regions"   : sorted(df["Region"].dropna().unique().tolist())
                      if "Region" in df.columns else [],
        "segments"  : sorted(df["Segment"].dropna().unique().tolist())
                      if "Segment" in df.columns else [],
        "categories": sorted(df["Category"].dropna().unique().tolist())
                      if "Category" in df.columns else [],
        "date_range": (
            f"{df['Order_Date'].min().strftime('%b %Y')} → "
            f"{df['Order_Date'].max().strftime('%b %Y')}"
            if "Order_Date" in df.columns
            and pd.api.types.is_datetime64_any_dtype(df["Order_Date"])
            and df["Order_Date"].notna().any()
            else "N/A"
        ),
    }


def compute_campaign_comparison(df: pd.DataFrame) -> pd.DataFrame:
    if "Is_Campaign_Order" not in df.columns:
        return pd.DataFrame()
    comp = (
        df.groupby("Is_Campaign_Order")
          .agg(
              Orders      =("Sales",          "count"),
              Total_Sales =("Sales",          "sum"),
              Total_Profit=("Profit",         "sum"),
              Avg_Sales   =("Sales",          "mean"),
              Avg_Profit  =("Profit",         "mean"),
              Avg_Margin  =("Profit_Margin_", "mean"),
              Avg_Discount=("Discount",       "mean"),
          )
          .round(2)
          .reset_index()
    )
    comp["Type"] = comp["Is_Campaign_Order"].map(
        {True:"Campaign", False:"No Campaign",
         1:"Campaign",    0:"No Campaign"}
    )
    comp["Sales_Share_%"] = (
        comp["Total_Sales"] / comp["Total_Sales"].sum() * 100
    ).round(1)
    return comp.drop(columns="Is_Campaign_Order")