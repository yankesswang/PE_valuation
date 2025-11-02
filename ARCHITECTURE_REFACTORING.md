# Architecture Refactoring - Separation of Concerns

## Overview

The valuation system has been refactored to **separate data collection (scraping) from calculations**. This provides:
- ✅ Cleaner code architecture
- ✅ Faster analysis (no waiting for web scraping)
- ✅ Reproducible results (uses fixed dataset)
- ✅ Easier testing and debugging

## New Architecture

### Before (Old Design)
```
valuation_analyzer.py
  ├─ Loads some data from JSON files
  ├─ ALSO scrapes websites for additional data
  └─ Calculates valuations
```
**Problem:** Mixed responsibilities, slow, unpredictable

### After (New Design)
```
Step 1: DATA COLLECTION (Run periodically, e.g., daily/weekly)
  ├─ ratio_scraper_fixed.py      → stock_list_metrics_YYYY-MM-DD.json
  ├─ forecast_scraper_working.py → stock_list_forecasts_YYYY-MM-DD.json
  └─ pe_scraper.py               → stock_list_PE_YYYY-MM-DD.json

Step 2: ANALYSIS (Run anytime, instant)
  └─ valuation_analyzer_pure.py  → stock_data_YYYY-MM-DD.xlsx
      (Only reads JSON files, does calculations)
```

## File Descriptions

### Data Collection Scripts (Run Separately)

#### 1. `ratio_scraper_fixed.py`
**Purpose:** Collect financial metrics from StockAnalysis.com

**What it scrapes:**
- Market cap, enterprise value
- PE, PS, PB ratios
- Margins, cash flow metrics
- Beta, shares outstanding
- **Current stock price** (from yfinance)

**Output:** `../data/ratio/stock_list_metrics_YYYY-MM-DD.json`

**When to run:** Weekly or when you need updated metrics

**How to run:**
```bash
cd modules
python3 ratio_scraper_fixed.py
# Takes ~30-60 min for all stocks
```

#### 2. `forecast_scraper_working.py`
**Purpose:** Collect EPS and Revenue forecasts

**What it scrapes:**
- Current year EPS/Revenue forecasts
- Next year EPS/Revenue forecasts
- Growth rate forecasts

**Output:** `../data/forecast/stock_list_forecasts_YYYY-MM-DD.json`

**When to run:** Monthly or quarterly (forecasts don't change often)

**How to run:**
```bash
cd modules
python3 forecast_scraper_working.py
# or use regenerate_forecast_data.py
```

#### 3. `pe_scraper.py`
**Purpose:** Collect historical PE ratios

**What it scrapes:**
- 5-year historical PE ratios
- Calculates median PE

**Output:** `../data/pe/stock_list_PE_YYYY-MM-DD.json`

**When to run:** Quarterly (historical data changes slowly)

### Analysis Script (Run Anytime)

#### `valuation_analyzer_pure.py`
**Purpose:** Pure calculation engine - NO scraping

**What it does:**
- Loads latest JSON data files
- Calculates estimated PE based on growth
- Calculates fair values
- Compares to current price
- Generates valuation reports

**What it DOESN'T do:**
- ❌ No web scraping
- ❌ No external API calls (except yfinance which is optional)
- ❌ No data collection

**Input:** Pre-collected JSON files (automatic latest file detection)

**Output:** `../valuation/stock_data_YYYY-MM-DD.xlsx`

**How to run:**
```bash
cd modules
python3 valuation_analyzer_pure.py
# Runs instantly (no web scraping wait time!)
```

## Workflow

### Initial Setup (Once)
```bash
cd modules

# 1. Collect all data (takes ~1-2 hours total)
python3 ratio_scraper_fixed.py
python3 forecast_scraper_working.py
python3 pe_scraper.py

# 2. Run analysis (instant)
python3 valuation_analyzer_pure.py
```

### Regular Usage

**Weekly:**
```bash
# Update prices and current metrics
python3 ratio_scraper_fixed.py
python3 valuation_analyzer_pure.py
```

**Monthly:**
```bash
# Update forecasts
python3 forecast_scraper_working.py
python3 valuation_analyzer_pure.py
```

**Quarterly:**
```bash
# Full refresh
python3 ratio_scraper_fixed.py
python3 forecast_scraper_working.py
python3 pe_scraper.py
python3 valuation_analyzer_pure.py
```

## Key Improvements

### 1. Speed
- **Old:** 10-30 seconds per stock = 30-60 minutes for 153 stocks
- **New:** < 1 second per stock = ~10 seconds total for analysis

### 2. Reliability
- **Old:** Fails if website is down during analysis
- **New:** Uses pre-collected data, always works

### 3. Reproducibility
- **Old:** Different results each run (live data)
- **New:** Same results for same dataset (reproducible)

### 4. Testing
- **Old:** Hard to test (needs website access)
- **New:** Easy to test (just JSON files)

### 5. Data Management
- **Old:** Data scattered, no history
- **New:** All data files timestamped, can track changes over time

## Data File Structure

### Ratio Data
```json
{
  "NVDA": {
    "industry": "大科技",
    "marketcap": 4920507000000.0,
    "pe": 54.9,
    "beta": 1.67,
    "currentPrice": 202.49,
    // ... 58 total metrics
  }
}
```

### Forecast Data
```json
{
  "NVDA": {
    "annual": {
      "current_eps": 4.59,
      "next_year_eps": 6.59,
      "current_growth": 56.1,
      "next_year_growth": 43.69,
      "current_revenue": 210500000000.0,
      "next_year_revenue": 284000000000.0
    },
    "quarterly": {
      "eps": [],
      "revenue": []
    }
  }
}
```

### PE Data
```json
{
  "NVDA": 54.9,
  "AAPL": 28.3,
  "MSFT": 32.2
}
```

## Migration Guide

### From Old to New

**Old way:**
```python
from valuation_analyzer import Valuation_Analyzer
analyzer = Valuation_Analyzer(2025)
df_dict = analyzer.aggregate_company_data()
```

**New way:**
```python
from valuation_analyzer_pure import Valuation_Analyzer_Pure
from names import STOCK_LIST

analyzer = Valuation_Analyzer_Pure(2025)
df_dict = analyzer.aggregate_company_data(STOCK_LIST)
```

**Key Differences:**
1. Import from `valuation_analyzer_pure` instead
2. Pass `STOCK_LIST` to `aggregate_company_data()`
3. Make sure data files are pre-collected
4. Much faster execution!

## Important Notes

### Current Price Collection

The ratio scraper now includes current stock prices using yfinance. This means:

✅ **Pros:**
- All data in one place
- No real-time API calls during analysis

⚠️ **Cons:**
- Price is a snapshot from when scraper ran
- For real-time prices, consider adding a separate price update script

### Data Freshness

Remember:
- **Ratio metrics:** Update weekly (includes price)
- **Forecasts:** Update monthly
- **PE ratios:** Update quarterly

### Backwards Compatibility

The old `valuation_analyzer.py` still works but:
- ❌ Slower (does web scraping)
- ❌ Mixed responsibilities
- ✅ Use for emergency fallback only

## Recommended: Make New Analyzer the Default

```bash
cd modules

# Backup old analyzer
mv valuation_analyzer.py valuation_analyzer_old.py

# Make pure analyzer the default
cp valuation_analyzer_pure.py valuation_analyzer.py
```

Then update imports to just:
```python
from valuation_analyzer import Valuation_Analyzer_Pure as Valuation_Analyzer
```

## Summary

The new architecture provides:
- **Clear separation:** Scraping vs Calculation
- **Better performance:** 100x faster analysis
- **Easier maintenance:** Each module has one job
- **Data versioning:** Timestamped data files
- **Reproducibility:** Same data = same results

This is a **significant improvement** over the old mixed-responsibility design!
