# ============================================================
# core/cleaning.py — Production-grade data cleaning pipeline
# Handles any sales CSV format automatically
# ============================================================

import pandas as pd
import numpy as np
import logging

log = logging.getLogger(__name__)

COLUMN_ALIASES = {
    "order_id"     : "Order_ID",      "orderid"       : "Order_ID",
    "order_date"   : "Order_Date",    "orderdate"     : "Order_Date",
    "ship_date"    : "Ship_Date",     "shipdate"      : "Ship_Date",
    "ship_mode"    : "Ship_Mode",     "customer_id"   : "Customer_ID",
    "customer_name": "Customer_Name", "segment"       : "Segment",
    "region"       : "Region",        "category"      : "Category",
    "sub_category" : "Sub_Category",  "subcategory"   : "Sub_Category",
    "product_id"   : "Product_ID",    "product_name"  : "Product_Name",
    "sales"        : "Sales",         "revenue"       : "Sales",
    "quantity"     : "Quantity",      "qty"           : "Quantity",
    "discount"     : "Discount",      "profit"        : "Profit",
}

REQUIRED_COLS = ["Sales", "Profit", "Discount"]
NUMERIC_COLS  = ["Sales", "Profit", "Discount", "Quantity"]


def validate_dataframe(df: pd.DataFrame) -> tuple:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    return len(missing) == 0, missing


def parse_date_column(series: pd.Series, col_name: str) -> pd.Series:
    if series.dropna().empty:
        return pd.to_datetime(series, errors="coerce")

    sample = str(series.dropna().iloc[0]).strip()
    fmt    = None

    if "/" in sample:
        parts = sample.split("/")
        if len(parts) == 3:
            fmt = "%m/%d/%Y" if len(parts[2]) == 4 else "%m/%d/%y"
    elif "-" in sample:
        parts = sample.split("-")
        fmt   = "%Y-%m-%d" if len(parts[0]) == 4 else "%d-%m-%Y"

    if fmt:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        if parsed.isna().mean() <= 0.05:
            return parsed

    for fallback in ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d",
                     "%d-%m-%Y", "%Y/%m/%d", "%d-%b-%Y"]:
        parsed = pd.to_datetime(series, format=fallback, errors="coerce")
        if parsed.isna().mean() <= 0.05:
            return parsed

    return pd.to_datetime(series, errors="coerce")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
          .str.strip()
          .str.replace(r"[\s\-]+", "_", regex=True)
          .str.replace(r"[^\w]", "",   regex=True)
    )
    rename_map = {}
    for col in df.columns:
        alias = COLUMN_ALIASES.get(col.lower())
        if alias and alias not in df.columns:
            rename_map[col] = alias
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def enforce_numeric_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in NUMERIC_COLS:
        if col not in df.columns:
            continue
        df[col] = (
            df[col].astype(str)
                   .str.replace(r"[\$£€,\s]", "", regex=True)
                   .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def remove_duplicates(df: pd.DataFrame) -> tuple:
    before = len(df)
    for subset in [["Order_ID", "Product_ID"], ["Order_ID"], None]:
        available = (
            [c for c in subset if c in df.columns]
            if subset else None
        )
        if subset is None or (available and len(available) == len(subset)):
            df      = df.drop_duplicates(subset=available)
            removed = before - len(df)
            return df, removed
    return df, 0


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include="number").columns
    for col in num_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    cat_cols = df.select_dtypes(include="object").columns
    for col in cat_cols:
        if df[col].isna().sum() > 0 and not df[col].dropna().empty:
            df[col] = df[col].fillna(df[col].mode()[0])
    return df


def cap_outliers(df: pd.DataFrame) -> tuple:
    report = {}
    for col in ["Sales", "Profit"]:
        if col not in df.columns:
            continue
        Q1    = df[col].quantile(0.25)
        Q3    = df[col].quantile(0.75)
        IQR   = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        n_out = int(((df[col] < lower) | (df[col] > upper)).sum())
        df[col]     = df[col].clip(lower=lower, upper=upper)
        report[col] = {"outliers_capped": n_out,
                       "lower_bound"    : round(lower, 2),
                       "upper_bound"    : round(upper, 2)}
    return df, report


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    order_is_dt = pd.api.types.is_datetime64_any_dtype(
        df.get("Order_Date", pd.Series(dtype="object"))
    )
    ship_is_dt = pd.api.types.is_datetime64_any_dtype(
        df.get("Ship_Date", pd.Series(dtype="object"))
    )

    if order_is_dt:
        df["Order_Year"]       = df["Order_Date"].dt.year.astype("Int64")
        df["Order_Month"]      = df["Order_Date"].dt.month.astype("Int64")
        df["Order_Month_Name"] = df["Order_Date"].dt.strftime("%b")
        df["Order_Quarter"]    = df["Order_Date"].dt.quarter.astype("Int64")

    if order_is_dt and ship_is_dt:
        df["Delivery_Days"] = (
            df["Ship_Date"] - df["Order_Date"]
        ).dt.days.astype(float)
        df.loc[df["Delivery_Days"] < 0, "Delivery_Days"] = np.nan

    # Profit Margin
    df["Profit_Margin_"] = np.where(
        df["Sales"].abs() > 0.001,
        (df["Profit"] / df["Sales"] * 100).round(2),
        0.0
    )

    # Revenue per unit
    qty = (
        df["Quantity"].replace(0, np.nan)
        if "Quantity" in df.columns
        else pd.Series(1.0, index=df.index)
    )
    df["Revenue_per_Unit"] = (df["Sales"] / qty).round(2).fillna(0.0)

    # Campaign flag
    df["Is_Campaign_Order"] = (df["Discount"] > 0).astype(bool)

    # Discount band
    df["Discount_Band"] = pd.cut(
        df["Discount"],
        bins   = [-0.001, 0, 0.10, 0.20, 0.30, 0.50, 1.0],
        labels = ["No Discount","1-10%","11-20%","21-30%","31-50%","51%+"],
    )

    # Profit category
    df["Profit_Category"] = pd.cut(
        df["Profit_Margin_"],
        bins   = [-np.inf, 0, 10, 25, np.inf],
        labels = ["Loss","Low Margin","Healthy","High Margin"],
    )

    return df


def clean_dataframe(df: pd.DataFrame) -> tuple:
    """
    Full cleaning pipeline.
    Returns (cleaned_df, cleaning_report_dict)
    """
    report = {
        "rows_before": len(df), "cols_before": len(df.columns),
        "duplicates" : 0,       "outliers"   : {},
        "errors"     : [],      "warnings"   : [],
    }
    try:
        df = standardize_columns(df)
        df = enforce_numeric_types(df)

        for col in ["Order_Date", "Ship_Date"]:
            if col in df.columns:
                df[col] = parse_date_column(df[col], col)

        df, dupes            = remove_duplicates(df)
        report["duplicates"] = dupes

        df               = handle_missing_values(df)
        df, outlier_rpt  = cap_outliers(df)
        report["outliers"]   = outlier_rpt

        df = engineer_features(df)

        report["rows_after"]   = len(df)
        report["cols_after"]   = len(df.columns)
        report["rows_removed"] = report["rows_before"] - len(df)

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        log.error("Cleaning error: %s", e)
        report["errors"].append(str(e))

    return df, report