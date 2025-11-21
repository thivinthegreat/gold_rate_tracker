# Gold & Silver Price Tracker

This repository scrapes 10-day price data from The Jewellers Association
and maintains a full historical record.

## Structure

- `scraper.py` — Scrapes data, updates CSV, generates JSON
- `data/history.csv` — Full historical dataset
- `data/latest.json` — Latest day snapshot with stats
- `data/history.json` — JSON version of full history
- `.github/workflows/update.yml` — GitHub Action (to be added later)

