# Stock Valuation Analysis Tool

A Python-based stock valuation analyzer that scrapes financial data from multiple sources and generates comprehensive valuation reports based on PE ratios, growth forecasts, and historical metrics.

## Features

- **Multi-source Data Scraping**: Automatically collects financial data from StockAnalysis.com and Yahoo Finance
- **Comprehensive Metrics Collection**:
  - 5-year historical PE ratios
  - Market capitalization and current prices
  - Revenue and EPS growth forecasts
  - Beta values and other financial ratios
- **Intelligent Valuation Analysis**:
  - Growth-based PE estimation with adjustable multipliers
  - 5-year PE median calculations
  - Current year and next year valuation comparisons
  - Overvalued/undervalued assessments with percentage differences
- **Industry-organized Reports**: Generates Excel files with data organized by industry sectors
- **Parallel Processing**: Runs multiple scrapers concurrently for faster data collection

## Installation

### Prerequisites

- Python 3.7+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer (recommended)
  - Install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd PE_valuation
```

2. Create a virtual environment and install dependencies using uv:
```bash
uv venv
uv pip install -r requirements.txt
```

3. Activate the virtual environment:
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

#### Alternative: Traditional pip setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### 1. Collect Stock Data

Run the parallel scraper to collect all necessary data:

```bash
cd modules
python3 sub_process.py
```

This will execute three scrapers in parallel:
- `ratio_scraper.py` - Collects financial ratios and metrics
- `pe_scraper.py` - Retrieves 5-year PE ratio data
- `forecast_scraper.py` - Gathers growth forecasts

Data will be saved to the `data/` directory organized by type.

### 2. Generate Valuation Analysis

Run the valuation analyzer to process the collected data:

```bash
cd modules
python3 valuation_analyzer.py
```

This will:
- Process all companies in your stock list
- Calculate valuation metrics
- Generate an Excel report in the `valuation/` directory

### 3. Single Stock Analysis

To analyze a specific stock:

```python
from modules.valuation_analyzer import Valuation_Analyzer

analyzer = Valuation_Analyzer(2025)  # Current year
result = analyzer.process_company('AAPL')
print(result)
```

## Project Structure

```
PE_valuation/
├── modules/
│   ├── data_scraper.py          # Main scraper class for stock analysis
│   ├── ratio_scraper.py         # Financial ratios collector
│   ├── forecast_scraper.py      # Growth forecasts scraper
│   ├── pe_scraper.py            # PE ratio historical data
│   ├── valuation_analyzer.py    # Core valuation logic
│   ├── sub_process.py           # Parallel scraper executor
│   ├── utils.py                 # Helper functions
│   └── names.py                 # Stock lists and constants
├── data/
│   ├── pe/                      # PE ratio data (JSON)
│   ├── ratio/                   # Financial metrics (JSON)
│   └── forecast/                # Growth forecasts (JSON)
├── valuation/                   # Generated Excel reports
├── main.py                      # Example usage script
└── requirements.txt             # Python dependencies
```

## Data Sources

- **StockAnalysis.com**: Primary source for financial metrics, forecasts, and PE ratios
- **Yahoo Finance**: Stock prices and market data via yfinance library

## Valuation Methodology

### Growth-based PE Estimation

The tool calculates estimated PE ratios based on 5-year EPS growth forecasts:

| EPS Growth Rate | PE Multiplier |
|----------------|---------------|
| 0-5%           | 0.8x growth   |
| 5-10%          | 1.0x growth   |
| 10-15%         | 1.1x growth   |
| 15-20%         | 1.2x growth   |
| 20-30%         | 1.5x growth   |
| 30%+           | 2.0x growth   |

### Valuation Metrics

For each stock, the analyzer calculates:
- Current year and next year EPS estimates
- Fair value based on estimated PE
- Fair value based on 5-year median PE
- Valuation assessment (overvalued/undervalued)
- Percentage difference from fair value

## Output Format

The generated Excel file contains:
- One worksheet per industry sector
- Transposed format with companies as columns
- Metrics including:
  - Revenue Growth Forecast (5Y)
  - EPS Growth Forecast (5Y)
  - Estimated PE
  - Current/Next year EPS and fair prices
  - 5-year PE median and median price
  - Market cap and current stock price
  - Valuation status and percentage differences

## Configuration

Edit `modules/names.py` to customize:
- Stock lists by industry
- Ratio names to scrape
- Forecast metrics to collect

## Notes

- The scrapers include random delays (10-30 seconds) between requests to avoid rate limiting
- Historical data files are timestamped for tracking
- Ensure stable internet connection during scraping operations
- Some stocks may not have complete data available

## Dependencies

- `pandas` - Data manipulation and Excel export
- `selenium` - Web scraping automation
- `webdriver-manager` - Automatic WebDriver management
- `tqdm` - Progress bars
- `yfinance` - Yahoo Finance data access
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP library for API calls
- `numpy` - Numerical computations
- `json5` - JSON5 parsing
- `xlsxwriter` - Excel file generation
- `lxml` - XML/HTML processing

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
