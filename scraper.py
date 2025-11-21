#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scraper.py
----------
Fetches last 10–30 days of gold/silver prices from JAJ website, 
and computes full PRO PACK technical indicators:

✓ SMA7, SMA20, SMA30
✓ EMA12, EMA26
✓ MACD (Line, Signal, Histogram)
✓ RSI-14
✓ Bollinger Bands (20-SMA ± 2 SD)

Outputs:
    data/history.csv
    data/history.json
    data/latest.json
"""

import os
import random
import time
import json
import logging
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ---------------------------------------
# Logging
# ---------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ---------------------------------------
# User agents
# ---------------------------------------
USER_AGENTS = [
    # Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
    # Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
]

def get_agent():
    return random.choice(USER_AGENTS)


# ---------------------------------------
# Safe HTTP
# ---------------------------------------
def safe_get(url, retries=3, timeout=20):
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": get_agent(),
                    "Accept-Language": "en-US,en;q=0.9",
                },
                timeout=timeout
            )
            logger.info(f"GET success: {url}")
            return response
        except Exception as e:
            logger.warning(f"GET failed (attempt {attempt+1}): {e}")
            time.sleep(1 + attempt)
    logger.error("GET failed after retries.")
    return None


# ---------------------------------------
# URL builder (10-day window)
# ---------------------------------------
def build_url(days=15, page=1):
    today = datetime.now()
    from_date = (today - timedelta(days=days)).strftime("%d/%m/%Y")
    to_date = today.strftime("%d/%m/%Y")
    logger.info(f"Start Date :  {from_date}")
    logger.info(f"End Date : {to_date}")
    


    base = "https://www.thejewellersassociation.org/searchresult.php"
    params = (
        f"type=ratesearch&from_date={from_date}&to_date={to_date}"
        f"&commodity=3&rate_timing=1&page={int(page)}"
    )

    final_url =  f"{base}?{params}#location"

    logger.info(f"Final URL : {final_url}")
    return final_url


# ---------------------------------------
# Scrape HTML table
# ---------------------------------------
def scrape_table():
    

    
    # replace "#location" with "&page={}#location" 
    for page in range(1, 13):
        url = build_url(180, page)
        print("getting Page : ", page)
        resp = safe_get(url)
        if resp is None:
            return pd.DataFrame()

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.result_table")

        if table is None:
            logger.error("result_table not found.")
            return pd.DataFrame()

        rows = table.select("tr")[1:]  # skip header
        data = []

        for tr in rows:
            cols = [c.text.strip() for c in tr.select("td")]
            if len(cols) < 6:
                continue

            raw_date = cols[1].split(" ")[0]  # "05/11/2025"
            date = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")

            gold = float(cols[2])
            silver = float(cols[4])

            data.append({
                "date": date,
                "gold": gold,
                "silver": silver
            })

    df = pd.DataFrame(data)
    logger.info(f"Scraped {len(df)} rows.")
    return df.sort_values("date")


# ---------------------------------------
# Indicator Calculations
# ---------------------------------------
def compute_indicators(df):
    """
    Computes indicators and replaces NaN with None for JSON and empty field for CSV.
    """

    def compute_one(df, col):

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
        df[f"rsi14_{col}"] = 100 - (100 / (1 + rs))

        # Bollinger
        sma20 = df[col].rolling(20).mean()
        std20 = df[col].rolling(20).std()

        df[f"boll_sma20_{col}"] = sma20
        df[f"boll_upper_{col}"] = sma20 + (2 * std20)
        df[f"boll_lower_{col}"] = sma20 - (2 * std20)

        return df

    df = compute_one(df, "gold")
    df = compute_one(df, "silver")

    # Replace NaN → None for JSON
    df = df.where(pd.notnull(df), None)

    return df

# ---------------------------------------
# JSON writers
# ---------------------------------------
def write_json(df):
    # HISTORY JSON
    hist_records = df.to_dict(orient="records")
    with open("data/history.json", "w") as f:
        json.dump(hist_records, f, indent=2)

    # LATEST JSON
    last = df.iloc[-1]

    latest_json = {
        "date": last["date"],
        "gold_rate": last["gold"],
        "silver_rate": last["silver"],
        "gold_up": bool(df["gold"].diff().iloc[-1] > 0),
        "silver_up": bool(df["silver"].diff().iloc[-1] > 0),
        "gold_weekly": float(df["gold"].rolling(7).mean().iloc[-1]),
        "silver_weekly": float(df["silver"].rolling(7).mean().iloc[-1])
    }

    with open("data/latest.json", "w") as f:
        json.dump(latest_json, f, indent=2)

    logger.info("Saved latest.json & history.json.")


# ---------------------------------------
# MAIN
# ---------------------------------------
def main():
    logger.info("=== Starting Scraper ===")

    # df = scrape_table()
    # if df.empty:
    #     logger.error("No data scraped. Aborting.")
    #     return
    df = pd.read_csv("data/history.csv")
    # Compute indicators
    df = compute_indicators(df)

    # Reset history.csv
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/history.csv", index=False)
    logger.info("Wrote fresh history.csv")

    # Write JSON files
    # write_json(df)

    logger.info("=== Scraper complete. ===")


if __name__ == "__main__":
    main()
