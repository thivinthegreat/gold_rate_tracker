#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scraper.py — FINAL CLEAN VERSION
---------------------------------
✓ Appends ONLY missing dates
✓ Uses IST timezone for daily check
✓ Keeps history.json untouched
✓ latest.json contains ALL technical indicators
✓ Consistent datetime handling
✓ No NaN in JSON (converted to None)
✓ history.csv stored as DD/MM/YYYY but internally datetime64
"""

import os
import random
import time
import json
import logging
from datetime import datetime, timedelta
import pytz

import pandas as pd
import requests
from bs4 import BeautifulSoup


# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# -------------------------------------------------
# Timezone helper
# -------------------------------------------------
IST = pytz.timezone("Asia/Kolkata")

def today_ist():
    return datetime.now(IST).date()


# -------------------------------------------------
# User Agents
# -------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

def get_agent():
    return random.choice(USER_AGENTS)


# -------------------------------------------------
# Safe HTTP GET
# -------------------------------------------------
def safe_get(url, retries=3, timeout=20):
    for attempt in range(retries):
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": get_agent()},
                timeout=timeout
            )
            return resp
        except Exception as e:
            logger.warning(f"[WARN] GET attempt {attempt+1} failed: {e}")
            time.sleep(1 + attempt)
    logger.error("[ERROR] Failed after retries.")
    return None


# -------------------------------------------------
# Build range URL
# -------------------------------------------------
def build_range_url(from_date, to_date, page=1):
    """
    Dates must be DD/MM/YYYY
    """
    base = "https://www.thejewellersassociation.org/searchresult.php"
    return (
        f"{base}?type=ratesearch&from_date={from_date}"
        f"&to_date={to_date}&commodity=3&rate_timing=1&page={page}#location"
    )


# -------------------------------------------------
# SCRAPE ANY DATE RANGE (returns datetime64 DF)
# -------------------------------------------------
def scrape_range(from_date_str, to_date_str):
    """
    Input : "22/11/2025" to "24/11/2025"
    Output DF columns: date(datetime64), gold(int), silver(int)
    """
    data = []

    # Try up to 5 pages
    for page in range(1, 6):
        url = build_range_url(from_date_str, to_date_str, page)
        resp = safe_get(url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.result_table")
        if not table:
            break

        rows = table.select("tr")[1:]
        if not rows:
            break

        for tr in rows:
            cols = [c.text.strip() for c in tr.select("td")]
            if len(cols) < 6:
                continue

            raw_date = cols[1].split(" ")[0]  # "05/11/2025"
            date = datetime.strptime(raw_date, "%d/%m/%Y")  # datetime object

            gold = int(float(cols[2]))
            silver = int(float(cols[4]))

            data.append({"date": date, "gold": gold, "silver": silver})

    df = pd.DataFrame(data)
    if df.empty:
        return df

    df = df.sort_values("date").reset_index(drop=True)
    return df


# -------------------------------------------------
# Indicator Calculations (returns df with indicators)
# -------------------------------------------------
def compute_indicators(df):

    def add(col):
        # SMA
        df[f"sma7_{col}"] = df[col].rolling(7).mean()
        df[f"sma20_{col}"] = df[col].rolling(20).mean()
        df[f"sma30_{col}"] = df[col].rolling(30).mean()

        # EMA
        df[f"ema12_{col}"] = df[col].ewm(span=12, adjust=False).mean()
        df[f"ema26_{col}"] = df[col].ewm(span=26, adjust=False).mean()

        # MACD
        df[f"macd_{col}"] = df[f"ema12_{col}"] - df[f"ema26_{col}"]
        df[f"macd_signal_{col}"] = df[f"macd_{col}"].ewm(span=9, adjust=False).mean()
        df[f"macd_hist_{col}"] = df[f"macd_{col}"] - df[f"macd_signal_{col}"]

        # RSI
        delta = df[col].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / (avg_loss + 1e-9)
        df[f"rsi14_{col}"] = 100 - 100 / (1 + rs)

        # Bollinger
        sma20 = df[col].rolling(20).mean()
        std20 = df[col].rolling(20).std()
        df[f"boll_upper_{col}"] = sma20 + 2 * std20
        df[f"boll_lower_{col}"] = sma20 - 2 * std20

    add("gold")
    add("silver")

    # Convert NaN → None for JSON safety
    df = df.where(pd.notnull(df), None)

    # Round floats
    num_cols = df.select_dtypes(include="float").columns
    df[num_cols] = df[num_cols].round(2)

    return df


# -------------------------------------------------
# latest.json writer — full record
# -------------------------------------------------
def write_latest_json(df):
    last = df.iloc[-1].to_dict()

    # FIX: convert Timestamp → string (DD/MM/YYYY)
    if isinstance(last.get("date"), pd.Timestamp):
        last["date"] = last["date"].strftime("%d/%m/%Y")

    with open("data/latest.json", "w") as f:
        json.dump(last, f, indent=2)

    logger.info("latest.json updated")

# -------------------------------------------------
# history.json writer — full record
# -------------------------------------------------
def write_history_json(df):
    """
    Writes processed 7-day history with full indicators.
    Output structure:
    {
        "1": { ... yesterday ... },
        "2": { ... },
        ...
        "7": { ... oldest ... }
    }
    """

    # Take last 7 rows
    last7 = df.tail(7).copy()

    # Convert Timestamp + NaN handling
    def json_safe(value):
        if isinstance(value, pd.Timestamp):
            return value.strftime("%d/%m/%Y")
        if value is None:
            return None
        return value

    # Prepare numbered dict
    out = {}

    # Reverse: last 7 rows, newest = key "1"
    for idx, (i, row) in enumerate(last7.iloc[::-1].iterrows(), start=1):
        row_dict = {k: json_safe(v) for k, v in row.to_dict().items()}
        out[str(idx)] = row_dict

    # Write file
    with open("data/history.json", "w") as f:
        json.dump(out, f, indent=2)

    logger.info("history.json (7-day processed) updated")


# -------------------------------------------------
# MAIN SCRAPER LOGIC
# -------------------------------------------------
def main():
    logger.info("=== Scraper Started ===")

    # Load existing history
    if not os.path.exists("data/history.csv"):
        logger.error("history.csv missing. Please bootstrap first.")
        return

    df_old = pd.read_csv("data/history.csv")

    # Convert back to datetime
    df_old["date"] = pd.to_datetime(df_old["date"], format="%d/%m/%Y")
    df_old = df_old.sort_values("date").reset_index(drop=True)

    last_date = df_old.iloc[-1]["date"].date()
    today = today_ist()

    logger.info(f"Last saved date (CSV): {last_date}")
    logger.info(f"Today's IST date:      {today}")

    # Already up-to-date
    if last_date >= today:
        logger.info("No new data needed.")
        write_latest_json(df_old)
        return

    # Missing days → fetch from last_date+1 → today
    from_date = (last_date + timedelta(days=1)).strftime("%d/%m/%Y")
    to_date = today.strftime("%d/%m/%Y")

    logger.info(f"Fetching new range: {from_date} → {to_date}")

    df_new = scrape_range(from_date, to_date)

    if df_new.empty:
        logger.warning("No rows found for missing days.")
        return

    # Check if today's row exists
    if df_new.iloc[-1]["date"].date() != today:
        logger.warning("Today's rate NOT available on website.")
        return

    # Merge
    df = pd.concat([df_old, df_new], ignore_index=True)
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)

    # Compute full indicators
    df = compute_indicators(df)

    # Save updated history in CSV format dd/mm/YYYY
    df_to_save = df.copy()
    df_to_save["date"] = df_to_save["date"].dt.strftime("%d/%m/%Y")
    df_to_save.to_csv("data/history.csv", index=False)
    logger.info("history.csv updated")

    # latest.json ONLY — DO NOT TOUCH history.json
    write_latest_json(df)
    logger.info("Completed writing latest.json")

    # Write processed 7-day history.json
    write_history_json(df)
    logger.info("Completed writing history.json")

    logger.info("=== Scraper Finished ===")


if __name__ == "__main__":
    main()
