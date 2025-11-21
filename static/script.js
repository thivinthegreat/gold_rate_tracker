
/* ============================================================================
   GLOBAL VARIABLES
============================================================================ */
let fullData = [];          // Entire CSV as array of objects
let chartGold = null;
let chartSilver = null;

/* ============================================================================
   1) CSV LOADER
============================================================================ */
async function loadCSV() {
    const res = await fetch("data/history.csv");
    const text = await res.text();
    const rows = text.trim().split("\n").map(r => r.split(","));

    const headers = rows[0];
    const output = [];

    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        let item = {};

        headers.forEach((h, idx) => {
            let v = row[idx];

            if (!isNaN(v) && v.trim() !== "") {
                // Convert numeric strings → float
                let num = parseFloat(v);
                item[h] = isNaN(num) ? null : num;
            }
            else if (v === "NaN" || v === "" || v === undefined) {
                item[h] = null;
            }
            else if (h === "date") {
                // Convert DD/MM/YYYY → Date object
                item[h] = v;
            }
            else {
                item[h] = v;
            }
        });

        output.push(item);
    }

    fullData = output;
}

/* ============================================================================
   2) RANGE HANDLER
============================================================================ */
function filterRange(days) {
    if (days === "ALL") return fullData;

    let cut = fullData.slice(-days);
    return cut;
}

/* ============================================================================
   3) BUILD BANNERS
============================================================================ */
function buildBanners() {
    const s = window.dashboardSummary;

    document.getElementById("bannerSection").innerHTML = `
        <!-- GOLD -->
        <div class="banner-card banner-gold">
            <div>
                <div class="banner-title">Gold (1g)</div>
                <div class="banner-value">₹${s.gold_price}</div>
                <div class="banner-change ${s.gold_dir}">
                    ${s.gold_dir === "up" ? "↑" : "↓"} ${s.gold_change}
                    <span class="text-sm opacity-70">(${s.gold_pct}%)</span>
                </div>
                <div class="text-sm opacity-80">Prev: ₹${s.gold_prev}</div>
                <div class="text-sm opacity-80">Weekly Avg: ₹${s.gold_weekly ?? "-"}</div>
            </div>
            <img src="static/gold.svg" class="banner-icon"/>
        </div>



        <!-- SILVER -->
        <div class="banner-card banner-silver">
            <div>
                <div class="banner-title">Silver (1g)</div>
                <div class="banner-value">₹${s.silver_price}</div>
                <div class="banner-change ${s.silver_dir}">
                    ${s.silver_dir === "up" ? "↑" : "↓"} ${s.silver_change}
                    <span class="text-sm opacity-70">(${s.silver_pct}%)</span>
                </div>
                <div class="text-sm opacity-80">Prev: ₹${s.silver_prev}</div>
                <div class="text-sm opacity-80">Weekly Avg: ₹${s.silver_weekly ?? "-"}</div>
            </div>
            <img src="static/silver.svg" class="banner-icon"/>
        </div>

    `;
}

/* ============================================================================
   4) BUILD CHARTS
============================================================================ */
function createChart(ctx, labelMap, data) {
    const labels = data.map(d => d.date);

    const datasets = [];

    for (const [label, config] of Object.entries(labelMap)) {
        datasets.push({
            label: label,
            data: data.map(d => d[config.key] ?? null),
            borderColor: config.color,
            backgroundColor: config.bg,
            tension: 0.15,
            fill: config.fill || false,
            borderWidth: config.width || 2
        });
    }

    return new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "nearest",
                intersect: false
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: { usePointStyle: true }
                },
                tooltip: {
                    mode: "index",
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: { callback: (v) => "₹" + v }
                }
            }
        }
    });
}

/* ============================================================================
   GOLD CHART
============================================================================ */
function buildGoldChart(data) {
    if (chartGold !== null) chartGold.destroy();

    const ctx = document.getElementById("goldChart").getContext("2d");

    const colors = {
        price: "#FFD700",
        sma7: "#f8b400",
        sma20: "#e59e0b",
        ema12: "#ff8a00",
        ema26: "#d97706"
    };

    chartGold = createChart(ctx, {
        "Gold Price": { key: "gold", color: colors.price, bg: "rgba(255,215,0,0.3)", fill: true },
        "SMA 7": { key: "sma7_gold", color: colors.sma7 },
        "SMA 20": { key: "sma20_gold", color: colors.sma20 },
        "EMA 12": { key: "ema12_gold", color: colors.ema12 },
        "EMA 26": { key: "ema26_gold", color: colors.ema26 }
    }, data);
}

/* ============================================================================
   SILVER CHART
============================================================================ */
function buildSilverChart(data) {
    if (chartSilver !== null) chartSilver.destroy();

    const ctx = document.getElementById("silverChart").getContext("2d");

    const colors = {
        price: "#C0C0C0",
        sma7: "#A9A9A9",
        sma20: "#909090",
        ema12: "#666666",
        ema26: "#4b5563"
    };

    chartSilver = createChart(ctx, {
        "Silver Price": { key: "silver", color: colors.price, bg: "rgba(192,192,192,0.3)", fill: true },
        "SMA 7": { key: "sma7_silver", color: colors.sma7 },
        "SMA 20": { key: "sma20_silver", color: colors.sma20 },
        "EMA 12": { key: "ema12_silver", color: colors.ema12 },
        "EMA 26": { key: "ema26_silver", color: colors.ema26 }
    }, data);
}

/* ============================================================================
   5) BUILD TABLE
============================================================================ */
function buildTable(data) {
    const tbody = document.getElementById("tableBody");
    tbody.innerHTML = "";

    data.slice().reverse().forEach(row => {
        tbody.innerHTML += `
        <tr>
            <td>${row.date}</td>
            <td>${row.gold ?? ""}</td>
            <td>${row.silver ?? ""}</td>
        </tr>`;
    });
}

/* ============================================================================
   6) RANGE BUTTON CLICK HANDLER
============================================================================ */
function loadRange(days, btn = null) {
    // highlight correct button
    document.querySelectorAll(".range-btn").forEach(b => b.classList.remove("selected"));
    if (btn) btn.classList.add("selected");

    let data = filterRange(days);
    buildGoldChart(data);
    buildSilverChart(data);
    buildTable(data);
}

/* ============================================================================
   7) DECISION METRICS HANDLER
============================================================================ */
async function loadBuyInsights() {
    try {
        const resp = await fetch("data/decision.json");
        const data = await resp.json();

        const gold = data.gold;
        const silver = data.silver;

        document.getElementById("latestDate").textContent = "Latest Date: " + data.gold.date;
        document.getElementById("topLatestUpdate").textContent =
    "📅 Latest Update: " + data.gold.date;



        // ------------ GOLD ------------
        document.getElementById("goldScoreValue").textContent = gold.buy_score;
        document.getElementById("goldMeterFill").style.width = gold.buy_score + "%";

        document.getElementById("goldRecommendation").textContent = gold.recommendation;

        document.getElementById("goldWeeklyAvg").textContent = gold.weekly_avg;
        document.getElementById("goldWeeklyDiff").innerHTML = coloredPct(gold.weekly_difference_pct);
        
        


        document.getElementById("goldMonthlyAvg").textContent = gold.monthly_avg;
        document.getElementById("goldMonthlyDiff").innerHTML = coloredPct(gold.monthly_difference_pct);

        document.getElementById("goldRSI").textContent = gold.rsi14;
        document.getElementById("goldBoll").textContent = gold.boll_position_pct + "%";
        document.getElementById("goldSMA20").innerHTML = coloredPct(gold.sma20_distance_pct);

        document.getElementById("goldReasoning").textContent = gold.reasoning;


        // ------------ SILVER ------------
        document.getElementById("silverScoreValue").textContent = silver.buy_score;
        document.getElementById("silverMeterFill").style.width = silver.buy_score + "%";

        document.getElementById("silverRecommendation").textContent = silver.recommendation;

        document.getElementById("silverWeeklyAvg").textContent = silver.weekly_avg;
        document.getElementById("silverWeeklyDiff").innerHTML = coloredPct(silver.weekly_difference_pct);
        




        document.getElementById("silverMonthlyAvg").textContent = silver.monthly_avg;
        document.getElementById("silverMonthlyDiff").innerHTML = coloredPct(silver.monthly_difference_pct);

        document.getElementById("silverRSI").textContent = silver.rsi14;
        document.getElementById("silverBoll").textContent = silver.boll_position_pct + "%";
        document.getElementById("silverSMA20").innerHTML = coloredPct(silver.sma20_distance_pct);

        document.getElementById("silverReasoning").textContent = silver.reasoning;


    } catch (err) {
        console.error("Insights load failed:", err);
    }
}

function formatPct(val) {
    if (val == null) return "--";
    return (val >= 0 ? "+" : "") + val + "%";
}

function coloredPct(val) {
    if (val == null) return "--";
    
    const arrow = val > 0 ? "↑" : (val < 0 ? "↓" : "→");
    const cls = val > 0 ? "pct-pos" : (val < 0 ? "pct-neg" : "pct-zero");

    return `<span class="${cls}">${arrow} ${val}%</span>`;
}

document.addEventListener("DOMContentLoaded", loadBuyInsights);




/* ============================================================================
   7) FULL HISTORY TABLE LOADER
============================================================================ */
function loadFullTable() {
    buildTable(fullData);
}

/* ============================================================================
   INIT
============================================================================ */
(async function init() {
    await loadCSV();
    buildBanners();
    loadRange(30);
})();
