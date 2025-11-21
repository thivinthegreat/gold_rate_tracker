#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_html.py
-----------------
Generates the index.html file for the dashboard.
All CSS and JS live in /static/style.css and /static/script.js.
Data is loaded inside JS using fetch("data/history.csv").

This file:
- Loads history.csv
- Extracts latest record
- Computes price changes
- Injects summary values into an inline JSON in index.html
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# --------------------------------------
# Load CSV
# --------------------------------------
df = pd.read_csv("data/history.csv")
df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
df = df.sort_values("date").reset_index(drop=True)

latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) >= 2 else latest

gold_change = latest["gold"] - prev["gold"]
silver_change = latest["silver"] - prev["silver"]

gold_dir = "up" if gold_change > 0 else "down" if gold_change < 0 else "same"
silver_dir = "up" if silver_change > 0 else "down" if silver_change < 0 else "same"

gold_prev = prev["gold"]
silver_prev = prev["silver"]

gold_pct = (gold_change / gold_prev * 100) if gold_prev else 0
silver_pct = (silver_change / silver_prev * 100) if silver_prev else 0

summary = {
    "gold_price": int(latest["gold"]),
    "silver_price": int(latest["silver"]),

    "gold_prev": int(gold_prev),
    "silver_prev": int(silver_prev),

    "gold_change": int(gold_change),
    "silver_change": int(silver_change),

    "gold_pct": round(gold_pct, 2),
    "silver_pct": round(silver_pct, 2),

    "gold_dir": gold_dir,
    "silver_dir": silver_dir,

    "gold_weekly": latest.get("sma7_gold", None),
    "silver_weekly": latest.get("sma7_silver", None),
}

summary_json = json.dumps(summary)

# --------------------------------------
# Build index.html
# --------------------------------------
html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Gold & Silver Dashboard</title>

    <!-- TailwindCSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <!-- Custom CSS -->
    <link rel="stylesheet" href="assets/css/style.css">

</head>

<body class="bg-[#f4f5f7] p-4 md:p-8">

    <!-- Summary data JSON -->
    <script>
        window.dashboardSummary = {summary_json};
    </script>

    <!-- HEADER -->
    <header class="header-bar mb-6">
        <div class="max-w-7xl mx-auto flex items-center justify-between py-4 px-3">
            <h1 class="header-title">Gold & Silver Dashboard</h1>
            <a href="https://github.com/thivinthegreat/gold_rate_tracker"
            target="_blank" class="github-link">
                View on GitHub →
            </a>
        </div>
    </header>

    <div id="app" class="max-w-7xl mx-auto">

        <div id="topLatestUpdate" class="top-latest-update">
        📅 Latest Update: --
     </div>
        
        <!-- ======== BANNERS ======== -->
        <div id="bannerSection" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"></div>

        <!-- ======== RANGE BUTTONS ======== -->
        <div class="flex flex-wrap justify-center gap-2 mb-8">
           <button onclick="loadRange(30, this)" class="range-btn selected">30 Days</button>
            <button onclick="loadRange(90, this)" class="range-btn">90 Days</button>
            <button onclick="loadRange(180, this)" class="range-btn">6 Months</button>
            <button onclick="loadRange(365, this)" class="range-btn">1 Year</button>
            <button onclick="loadRange('ALL', this)" class="range-btn">All</button>

        </div>

        <!-- ======== CHARTS ======== -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="card">
                <h2 class="chart-title">Gold Chart</h2>
                <div class="chart-container">
                    <canvas id="goldChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2 class="chart-title">Silver Chart</h2>
                <div class="chart-container">
                    <canvas id="silverChart"></canvas>
                </div>
            </div>
        </div>

        <!-- ===========================
            BUY INSIGHTS (GOLD & SILVER)
        ============================== -->
        <section id="buy-insights" class="insights-section">

            <div class="insight-header-bar">
                <h2 class="insights-title">Buy Insight Analysis</h2>
                <div id="latestDate" class="latest-date">Latest Date: --</div>
            </div>

            <div class="metal-pair">

                <!-- GOLD TILE -->
                <div class="metal-tile">
                    <h3 class="metal-header gold-header">Gold Analysis</h3>
                    
                    <div class="score-card">
                        <div class="score-value" id="goldScoreValue">--</div>
                        <div class="meter-bar"><div class="meter-fill" id="goldMeterFill"></div></div>
                        <div class="rec-text" id="goldRecommendation">--</div>
                    </div>

                    <div class="metrics-grid">
                        <div class="metric"><span>Weekly Avg</span><strong id="goldWeeklyAvg">--</strong><small id="goldWeeklyDiff">--</small></div>
                        <div class="metric"><span>Monthly Avg</span><strong id="goldMonthlyAvg">--</strong><small id="goldMonthlyDiff">--</small></div>
                        <div class="metric"><span>RSI 14</span><strong id="goldRSI">--</strong></div>
                        <div class="metric"><span>Bollinger</span><strong id="goldBoll">--</strong></div>
                        <div class="metric"><span>SMA20 Dist</span><strong id="goldSMA20">--</strong></div>
                    </div>

                    <details class="reasoning-box">
                        <summary>Detailed Reasoning</summary>
                        <p id="goldReasoning"></p>
                    </details>
                </div>

                <!-- SILVER TILE -->
                <div class="metal-tile">
                    <h3 class="metal-header silver-header">Silver Analysis</h3>
                    
                    <div class="score-card">
                        <div class="score-value" id="silverScoreValue">--</div>
                        <div class="meter-bar"><div class="meter-fill" id="silverMeterFill"></div></div>
                        <div class="rec-text" id="silverRecommendation">--</div>
                    </div>

                    <div class="metrics-grid">
                        <div class="metric"><span>Weekly Avg</span><strong id="silverWeeklyAvg">--</strong><small id="silverWeeklyDiff">--</small></div>
                        <div class="metric"><span>Monthly Avg</span><strong id="silverMonthlyAvg">--</strong><small id="silverMonthlyDiff">--</small></div>
                        <div class="metric"><span>RSI 14</span><strong id="silverRSI">--</strong></div>
                        <div class="metric"><span>Bollinger</span><strong id="silverBoll">--</strong></div>
                        <div class="metric"><span>SMA20 Dist</span><strong id="silverSMA20">--</strong></div>
                    </div>

                    <details class="reasoning-box">
                        <summary>Detailed Reasoning</summary>
                        <p id="silverReasoning"></p>
                    </details>
                </div>

            </div>

        </section>



        <!-- ======== TABLE ======== -->
        <div class="card mt-10">
            <h2 class="table-title">Price Table</h2>

            <div class="data-table-container overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Gold</th>
                            <th>Silver</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>

            <button onclick="loadFullTable()" class="full-btn">Show Full History</button>
        </div>

    </div>

    <!-- FOOTER -->
    <footer class="footer-bar mt-12 py-6">
        <div class="max-w-7xl mx-auto text-center text-sm footer-text px-4">
            <strong>Disclaimer:</strong>  
            This dashboard is for educational and personal use only.  
            Do not use this data for trading, financial decisions, or commercial purposes.  
            No accuracy or reliability is guaranteed.
        </div>
    </footer>

    <!-- Custom JS -->
   <script src="assets/js/script.js" defer></script>

</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html)

print("index.html generated successfully.")
