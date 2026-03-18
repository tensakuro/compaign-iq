# ============================================================
# core/database.py — SQLite with WAL mode + schema versioning
# ============================================================

import sqlite3
import pandas as pd
import numpy as np
import os
import logging

log        = logging.getLogger(__name__)
DB_PATH    = "data/campaign.db"
SCHEMA_VER = 2

DDL = """
CREATE TABLE IF NOT EXISTS sales (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    Order_ID          TEXT,   Order_Date        TEXT,
    Ship_Date         TEXT,   Ship_Mode         TEXT,
    Customer_ID       TEXT,   Customer_Name     TEXT,
    Segment           TEXT,   Region            TEXT,
    Category          TEXT,   Sub_Category      TEXT,
    Product_Name      TEXT,   Sales             REAL,
    Quantity          REAL,   Discount          REAL,
    Profit            REAL,   Profit_Margin_    REAL,
    Revenue_per_Unit  REAL,   Is_Campaign_Order INTEGER,
    Discount_Band     TEXT,   Profit_Category   TEXT,
    Order_Year        INTEGER,Order_Month       INTEGER,
    Order_Quarter     INTEGER,Delivery_Days     REAL
)
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_region   ON sales(Region)",
    "CREATE INDEX IF NOT EXISTS idx_segment  ON sales(Segment)",
    "CREATE INDEX IF NOT EXISTS idx_category ON sales(Category)",
    "CREATE INDEX IF NOT EXISTS idx_date     ON sales(Order_Date)",
    "CREATE INDEX IF NOT EXISTS idx_campaign ON sales(Is_Campaign_Order)",
    "CREATE INDEX IF NOT EXISTS idx_year     ON sales(Order_Year)",
    "CREATE INDEX IF NOT EXISTS idx_discount ON sales(Discount_Band)",
]


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        current = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()[0] or 0

        if current < SCHEMA_VER:
            conn.execute(DDL)
            for idx in INDEXES:
                conn.execute(idx)
            if current < 2:
                try:
                    conn.execute(
                        "ALTER TABLE sales "
                        "ADD COLUMN Profit_Category TEXT"
                    )
                except sqlite3.OperationalError:
                    pass
            conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (SCHEMA_VER,)
            )
            conn.commit()
    finally:
        conn.close()


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include="bool").columns:
        df[col] = df[col].astype(int)
    for col in df.select_dtypes(include="category").columns:
        df[col] = df[col].astype(str).replace("nan", None)
    for col in df.select_dtypes(include=["Int64","Int32"]).columns:
        df[col] = df[col].astype(object).where(df[col].notna(), None)
    for col in df.select_dtypes(include="datetime64").columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")
    df = df.replace([np.inf, -np.inf], np.nan)
    return df


def save_to_db(df: pd.DataFrame, db_path: str = DB_PATH):
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM sales")
        table_cols = [
            "Order_ID","Order_Date","Ship_Date","Ship_Mode",
            "Customer_ID","Customer_Name","Segment","Region",
            "Category","Sub_Category","Product_Name",
            "Sales","Quantity","Discount","Profit",
            "Profit_Margin_","Revenue_per_Unit","Is_Campaign_Order",
            "Discount_Band","Profit_Category","Order_Year",
            "Order_Month","Order_Quarter","Delivery_Days",
        ]
        save_cols = [c for c in table_cols if c in df.columns]
        _prep(df[save_cols]).to_sql(
            "sales", conn,
            if_exists="append", index=False,
            method="multi", chunksize=1000,
        )
        conn.commit()
        log.info("Saved %d rows to DB", len(df))
    except (sqlite3.DatabaseError, ValueError, TypeError) as e:
        conn.rollback()
        log.error("DB save failed: %s", e)
        raise
    finally:
        conn.close()


def run_query(sql: str, params: tuple = (),
              db_path: str = DB_PATH) -> pd.DataFrame:
    conn = get_connection(db_path)
    try:
        return pd.read_sql(sql, conn, params=params)
    except (sqlite3.DatabaseError, pd.errors.DatabaseError, ValueError) as e:
        log.error("Query error: %s", e)
        return pd.DataFrame()
    finally:
        conn.close()


# ── Pre-built queries ─────────────────────────────────────────
def query_regional(db_path=DB_PATH):
    return run_query("""
        SELECT Region,
            COUNT(*)                                       AS Orders,
            ROUND(SUM(Sales),2)                           AS Total_Sales,
            ROUND(SUM(Profit),2)                          AS Total_Profit,
            ROUND(AVG(Profit_Margin_),2)                  AS Avg_Margin,
            ROUND(AVG(CAST(Delivery_Days AS REAL)),1)     AS Avg_Delivery,
            ROUND(AVG(CAST(Is_Campaign_Order AS REAL))*100,1) AS Campaign_Pct
        FROM sales WHERE Region IS NOT NULL
        GROUP BY Region ORDER BY Total_Sales DESC
    """, db_path=db_path)


def query_segment(db_path=DB_PATH):
    return run_query("""
        SELECT Segment,
            COUNT(*)                      AS Orders,
            ROUND(SUM(Sales),2)           AS Total_Sales,
            ROUND(SUM(Profit),2)          AS Total_Profit,
            ROUND(AVG(Profit_Margin_),2)  AS Avg_Margin,
            ROUND(AVG(Sales),2)           AS Avg_Order
        FROM sales WHERE Segment IS NOT NULL
        GROUP BY Segment ORDER BY Total_Sales DESC
    """, db_path=db_path)


def query_monthly(db_path=DB_PATH):
    return run_query("""
        SELECT Order_Year, Order_Month,
            ROUND(SUM(Sales),2)  AS Sales,
            ROUND(SUM(Profit),2) AS Profit,
            COUNT(*)             AS Orders
        FROM sales
        WHERE Order_Year IS NOT NULL AND Order_Month IS NOT NULL
        GROUP BY Order_Year, Order_Month
        ORDER BY Order_Year, Order_Month
    """, db_path=db_path)


def query_discount_roi(db_path=DB_PATH):
    return run_query("""
        SELECT Discount_Band,
            COUNT(*)                      AS Orders,
            ROUND(AVG(Sales),2)           AS Avg_Sales,
            ROUND(AVG(Profit),2)          AS Avg_Profit,
            ROUND(AVG(Profit_Margin_),2)  AS Avg_Margin,
            ROUND(SUM(Sales),2)           AS Total_Revenue,
            ROUND(SUM(Profit),2)          AS Total_Profit,
            ROUND(AVG(Discount)*100,1)    AS Avg_Discount_Pct
        FROM sales
        WHERE Discount_Band NOT IN ('None','nan')
          AND Discount_Band IS NOT NULL
        GROUP BY Discount_Band
        ORDER BY CASE Discount_Band
            WHEN 'No Discount' THEN 1 WHEN '1-10%'  THEN 2
            WHEN '11-20%'      THEN 3 WHEN '21-30%' THEN 4
            WHEN '31-50%'      THEN 5 WHEN '51%+'   THEN 6
            ELSE 7 END
    """, db_path=db_path)


def query_top_products(n: int = 10, db_path: str = DB_PATH):
    # Use parameterized LIMIT to avoid SQL injection
    return run_query("""
        SELECT Sub_Category,
            ROUND(SUM(Sales),2)          AS Total_Sales,
            ROUND(SUM(Profit),2)         AS Total_Profit,
            ROUND(AVG(Profit_Margin_),2) AS Avg_Margin,
            COUNT(*)                     AS Orders
        FROM sales WHERE Sub_Category IS NOT NULL
        GROUP BY Sub_Category
        ORDER BY Total_Sales DESC LIMIT ?
    """, params=(int(n),), db_path=db_path)


def query_yoy(db_path=DB_PATH):
    return run_query("""
        SELECT Order_Year,
            ROUND(SUM(Sales),2)  AS Sales,
            ROUND(SUM(Profit),2) AS Profit,
            COUNT(*)             AS Orders
        FROM sales WHERE Order_Year IS NOT NULL
        GROUP BY Order_Year ORDER BY Order_Year
    """, db_path=db_path)