#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_html.py  (PART 1)
--------------------------
Builds index.html with:

✓ Dashboard header
✓ Summary cards
✓ GOLD + SILVER main charts
✓ SMA7 + SMA30 overlays
✓ Bollinger Bands (20-SMA ±2SD)
✓ Range filters

(Indicator tabs, recommendation engine, collapsible help section
will be injected in PART 2 and PART 3.)
"""

import json
from datetime import datetime
import math
import json

def clean_js_list(arr):
    safe = []
    for x in arr:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            safe.append("null")
        else:
            safe.append(int(round(x)))
    return safe


# -------------------------
# Date formatting helper
# -------------------------
def fmt(d):
    """2025-11-21 → 21-Nov-2025"""
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d-%b-%Y")


# -------------------------
# Main generator
# -------------------------
def generate_html():

    # ---- Load history & latest ----
    with open("data/history.json") as f:
        hist = json.load(f)

    with open("data/latest.json") as f:
        latest = json.load(f)

    # Arrays for charts
    dates = [row["date"] for row in hist]
    gold = [row["gold"] for row in hist]
    silver = [row["silver"] for row in hist]

    gold_change = latest["gold_rate"] - hist[-2]["gold"]
    silver_change = latest["silver_rate"] - hist[-2]["silver"]

    gold_change_fmt = f"+{int(gold_change)}" if gold_change > 0 else f"{int(gold_change)}"
    silver_change_fmt = f"+{int(silver_change)}" if silver_change > 0 else f"{int(silver_change)}"



    sma7_gold = clean_js_list([row["sma7_gold"] for row in hist])
    sma30_gold = clean_js_list([row["sma30_gold"] for row in hist])
    boll_upper_gold = clean_js_list([row["boll_upper_gold"] for row in hist])
    boll_lower_gold = clean_js_list([row["boll_lower_gold"] for row in hist])

    sma7_silver = clean_js_list([row["sma7_silver"] for row in hist])
    sma30_silver = clean_js_list([row["sma30_silver"] for row in hist])
    boll_upper_silver = clean_js_list([row["boll_upper_silver"] for row in hist])
    boll_lower_silver = clean_js_list([row["boll_lower_silver"] for row in hist])

    # -------------------------------
    # Build HTML (PART 1)
    # -------------------------------
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>

<title>Gold & Silver Dashboard</title>

<!-- Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- jQuery + DataTables (table comes later) -->
<script src="https://code.jquery.com/jquery-3.5.1.js"></script>
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css"/>
<script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>

<style>
body {{
    font-family: "Inter", sans-serif;
    margin: 0;
    background: #f2f3f7;
}}

h1 {{
    padding: 20px;
    margin: 0;
    text-align: center;
    background: #0d0d0d;
    color: white;
    font-size: 26px;
}}

.container {{
    max-width: 1100px;
    margin: auto;
    padding: 20px;
}}

.card-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    justify-content: center;
    margin-top: 20px;
}}

.card {{
    background: white;
    width: 180px;
    padding: 20px;
    text-align: center;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}

.card .value {{
    font-size: 32px;
    font-weight: 700;
}}

.up {{ color: green; }}
.down {{ color: red; }}

.range-buttons {{
    text-align: center;
    margin: 25px 0;
}}

.range-buttons button {{
    padding: 8px 14px;
    border-radius: 8px;
    border: 1px solid #aaa;
    background: white;
    cursor: pointer;
    margin: 4px;
}}

.range-buttons button:hover {{
    background: #eee;
}}

.chart-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
}}
@media(max-width: 800px) {{
    .chart-grid {{
        grid-template-columns: 1fr;
    }}
}}

.chart-box {{
    background: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    height: 380px;
}}
</style>

</head>
<body>

<h1>Gold & Silver Dashboard</h1>

<div class="container">

    <!-- Summary Cards -->
    <div class="card-grid">
        <div class="card">
            <div>Gold (1gm)</div>
            <div class="value">{latest["gold_rate"]}</div>
            <div class="{ 'up' if latest['gold_up'] else 'down' }">
                {'▲' if latest['gold_up'] else '▼'} {gold_change_fmt}
            </div>
            <small>Weekly Avg: {latest["gold_weekly"]}</small>
        </div>

        <div class="card">
            <div>Silver (1gm)</div>
            <div class="value">{latest["silver_rate"]}</div>
            <div class="{ 'up' if latest['silver_up'] else 'down' }">
                {'▲' if latest['silver_up'] else '▼'}{silver_change_fmt}
            </div>
            <small>Weekly Avg: {latest["silver_weekly"]}</small>
        </div>
    </div>

    <!-- Range Filters -->
    <div class="range-buttons">
        <button onclick="setRange(7)">Last Week</button>
        <button onclick="setRange(10)">10 Days</button>
        <button onclick="setRange(30)">30 Days</button>
        <button onclick="setRange(365)">1 Year</button>
        <button onclick="setRange('all')">All</button>
    </div>

    <!-- Main Price Charts -->
    <div class="chart-grid">
        <div class="chart-box"><canvas id="goldChart"></canvas></div>
        <div class="chart-box"><canvas id="silverChart"></canvas></div>
    </div>

"""

    # -------------------------------
    # JS (Charts) — Part 1 Only
    # -------------------------------
    html += f"""
<script>

const raw_dates = {dates};
const raw_gold = {gold};
const raw_silver = {silver};

const sma7_gold = {sma7_gold};
const sma30_gold = {sma30_gold};
const boll_upper_gold = {boll_upper_gold};
const boll_lower_gold = {boll_lower_gold};

const sma7_silver = {sma7_silver};
const sma30_silver = {sma30_silver};
const boll_upper_silver = {boll_upper_silver};
const boll_lower_silver = {boll_lower_silver};


// Gradient for area chart
function areaGradient(ctx, r, g, b) {{
    let grad = ctx.createLinearGradient(0,0,0,350);
    grad.addColorStop(0, "rgba(" + r + "," + g + "," + b + ",0.35)");
    grad.addColorStop(1, "rgba(" + r + "," + g + "," + b + ",0)");
    return grad;
}}

let goldChart, silverChart;

function buildMainCharts(dates, goldData, silverData) {{

    const goldCtx = document.getElementById("goldChart").getContext("2d");
    const silverCtx = document.getElementById("silverChart").getContext("2d");

    // ----- GOLD CHART -----
    goldChart = new Chart(goldCtx, {{
        type: 'line',
        data: {{
            labels: dates,
            datasets: [
                {{
                    label: "Gold",
                    data: goldData,
                    fill: true,
                    backgroundColor: areaGradient(goldCtx, 255,215,0),
                    borderColor: "rgba(255,215,0,1)",
                    borderWidth: 2,
                    tension: 0.25,
                }},
                {{
                    label: "SMA 7",
                    data: sma7_gold.slice(-dates.length),
                    borderColor: "#888",
                    borderWidth: 1.2,
                    fill: false,
                    tension: 0.2
                }},
                {{
                    label: "SMA 30",
                    data: sma30_gold.slice(-dates.length),
                    borderColor: "#444",
                    borderWidth: 1.2,
                    fill: false,
                    tension: 0.2
                }},
                {{
                    label: "Boll Upper",
                    data: boll_upper_gold.slice(-dates.length),
                    borderColor: "rgba(0,0,0,0.3)",
                    borderWidth: 1,
                    fill: false,
                    borderDash: [5,5]
                }},
                {{
                    label: "Boll Lower",
                    data: boll_lower_gold.slice(-dates.length),
                    borderColor: "rgba(0,0,0,0.3)",
                    borderWidth: 1,
                    fill: "-1",  // fill between this and previous dataset
                    backgroundColor: "rgba(200,200,200,0.15)"
                }},
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    display: false
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: false
                }}
            }}
        }}
    }});

    // ----- SILVER CHART -----
    silverChart = new Chart(silverCtx, {{
        type: 'line',
        data: {{
            labels: dates,
            datasets: [
                {{
                    label: "Silver",
                    data: silverData,
                    fill: true,
                    backgroundColor: areaGradient(silverCtx, 160,160,160),
                    borderColor: "rgba(160,160,160,1)",
                    borderWidth: 2,
                    tension: 0.25,
                }},
                {{
                    label: "SMA 7",
                    data: sma7_silver.slice(-dates.length),
                    borderColor: "#888",
                    borderWidth: 1.2,
                    fill: false,
                    tension: 0.2
                }},
                {{
                    label: "SMA 30",
                    data: sma30_silver.slice(-dates.length),
                    borderColor: "#444",
                    borderWidth: 1.2,
                    fill: false,
                    tension: 0.2
                }},
                {{
                    label: "Boll Upper",
                    data: boll_upper_silver.slice(-dates.length),
                    borderColor: "rgba(0,0,0,0.3)",
                    borderWidth: 1,
                    fill: false,
                    borderDash: [5,5]
                }},
                {{
                    label: "Boll Lower",
                    data: boll_lower_silver.slice(-dates.length),
                    borderColor: "rgba(0,0,0,0.3)",
                    borderWidth: 1,
                    fill: "-1",
                    backgroundColor: "rgba(200,200,200,0.15)"
                }},
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    display: false
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: false
                }}
            }}
        }}
    }});
}}


function updateRange(dates, goldData, silverData) {{
    goldChart.destroy();
    silverChart.destroy();
    buildMainCharts(dates, goldData, silverData);
}}

function setRange(days) {{
    if (days === 'all') {{
        updateRange(raw_dates, raw_gold, raw_silver);
        return;
    }}
    const cut = Math.max(0, raw_dates.length - days);

    updateRange(
        raw_dates.slice(cut),
        raw_gold.slice(cut),
        raw_silver.slice(cut)
    );
}}

// Build charts on load
buildMainCharts(raw_dates, raw_gold, raw_silver);

</script>

"""

    # END PART 1 — Note: Part 2 & 3 will append to HTML
    html += "\n<!-- PART 1 END -->\n"

    

    # Write file (unfinished)
    with open("index.html", "w") as f:
        f.write(html)

    print("Part 1 (layout + price charts) generated. Parts 2 & 3 pending.")


if __name__ == "__main__":
    generate_html()
