from utils import fetch_url, parse_html
import json, time, random
from datetime import datetime
from names import STOCK_LIST

class Forecast_Scraper_Working():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_date = datetime.now().strftime('%Y-%m-%d')

    def parse_value(self, value_str):
        """Parse a value string from the website into a numeric value"""
        if not value_str or value_str == 'n/a' or value_str == '-' or value_str == 'N/A' or 'Pro' in value_str:
            return None

        # Remove currency symbols, commas, and extra whitespace
        value_str = value_str.replace('$', '').replace(',', '').strip()

        try:
            # Handle percentage
            if '%' in value_str:
                return float(value_str.replace('%', ''))

            # Handle billions/millions/trillions
            multipliers = {'T': 1e12, 'B': 1e9, 'M': 1e6, 'K': 1e3}
            for suffix, multiplier in multipliers.items():
                if value_str.endswith(suffix):
                    return float(value_str[:-1]) * multiplier

            # Try direct conversion
            return float(value_str)
        except (ValueError, AttributeError):
            return None

    def extract_forecast_data(self, ticker, current_year=2025):
        """
        Extract EPS and Revenue forecast data for a given ticker from the forecast page.
        Args:
            ticker: Stock ticker symbol
            current_year: Current fiscal year (default 2025)
        """
        url = f"https://stockanalysis.com/stocks/{ticker}/forecast/"
        response = fetch_url(url, self.headers)

        if not response:
            print(f"Failed to fetch forecast data for {ticker}")
            return None

        soup = parse_html(response.text)
        forecast_data = {
            'annual': {
                'current_eps': None,
                'current_growth': None,
                'next_year_eps': None,
                'next_year_growth': None,
                'current_revenue': None,
                'current_revenue_growth': None,
                'next_year_revenue': None,
                'next_year_revenue_growth': None,
            },
            'quarterly': {
                'eps': [],
                'revenue': [],
                'revenue_growth': [],
                'eps_growth': [],
            }
        }

        # Find all tables
        tables = soup.find_all('table')

        # Process each table to find forecast tables (tables 5-8)
        for table in tables:
            # Get table header to identify what this table contains
            header_row = table.find('thead')
            if not header_row:
                continue

            headers = [th.get_text(strip=True) for th in header_row.find_all('th')]

            # Skip if not a forecast table (should have years as headers)
            if len(headers) < 2:
                continue

            # Identify table type by first header
            table_type = headers[0] if headers else ""

            # Get year columns (skip first column which is the label)
            year_headers = headers[1:]

            # Try to find year indices for current and next year
            try:
                current_year_idx = None
                next_year_idx = None
                current_year_str = str(current_year)
                next_year_str = str(current_year + 1)

                for idx, year_header in enumerate(year_headers):
                    if current_year_str in year_header:
                        current_year_idx = idx
                    if next_year_str in year_header:
                        next_year_idx = idx

                # If current year not found, use first available year (year_headers[0])
                if current_year_idx is None and len(year_headers) > 0:
                    # Check if first year is numeric and close to current year
                    try:
                        first_year = int(''.join(filter(str.isdigit, year_headers[0])))
                        if first_year >= current_year and first_year <= current_year + 2:
                            current_year_idx = 0
                            # Also adjust next year to be index 1 if available
                            if len(year_headers) > 1:
                                next_year_idx = 1
                    except:
                        pass

                # Still no current year? Skip this table
                if current_year_idx is None:
                    continue

            except (ValueError, IndexError):
                continue

            # Get table body rows
            body = table.find('tbody')
            if not body:
                continue

            rows = body.find_all('tr')

            # Find the "Avg" row (or first data row if Avg doesn't exist)
            avg_row = None
            for row in rows:
                cells = row.find_all('td')
                if cells and cells[0].get_text(strip=True) in ['Avg', 'Average']:
                    avg_row = cells
                    break

            # If no Avg row, try first data row
            if not avg_row and rows:
                avg_row = rows[0].find_all('td')

            if not avg_row or len(avg_row) < 2:
                continue

            # Extract values based on table type
            # Get current year value (index + 1 because first cell is label)
            current_val = None
            next_val = None

            if current_year_idx is not None and current_year_idx + 1 < len(avg_row):
                current_cell = avg_row[current_year_idx + 1]
                current_val = self.parse_value(current_cell.get('title') or current_cell.get_text(strip=True))

            if next_year_idx is not None and next_year_idx + 1 < len(avg_row):
                next_cell = avg_row[next_year_idx + 1]
                next_val = self.parse_value(next_cell.get('title') or next_cell.get_text(strip=True))

            # Store based on table type
            if 'EPS Growth' in table_type:
                forecast_data['annual']['current_growth'] = current_val
                forecast_data['annual']['next_year_growth'] = next_val

            elif 'EPS' in table_type and 'Growth' not in table_type:
                forecast_data['annual']['current_eps'] = current_val
                forecast_data['annual']['next_year_eps'] = next_val

            elif 'Revenue Growth' in table_type:
                forecast_data['annual']['current_revenue_growth'] = current_val
                forecast_data['annual']['next_year_revenue_growth'] = next_val

            elif 'Revenue' in table_type and 'Growth' not in table_type:
                forecast_data['annual']['current_revenue'] = current_val
                forecast_data['annual']['next_year_revenue'] = next_val

        print(f"Extracted forecast data for {ticker}")
        return forecast_data

    def get_company_metrics(self, current_year=2025):
        """Get forecast metrics for all companies in STOCK_LIST"""
        all_companies_forecasts = {}
        for industry, companies in STOCK_LIST.items():
            for company in companies:
                print(f"Fetching forecast data for {company}...")
                forecast = self.extract_forecast_data(company, current_year)
                if forecast:
                    all_companies_forecasts[company] = forecast
                # Wait to avoid rate limiting
                time.sleep(random.uniform(10, 30))
        return all_companies_forecasts

if __name__ == "__main__":
    scraper = Forecast_Scraper_Working()

    # Test with a single stock first
    print("Testing with NVDA...")
    test_result = scraper.extract_forecast_data("NVDA")
    print(f"\nTest result for NVDA:")
    print(json.dumps(test_result, indent=2))

    print("\n\nTesting with AAPL...")
    test_result2 = scraper.extract_forecast_data("AAPL")
    print(f"\nTest result for AAPL:")
    print(json.dumps(test_result2, indent=2))

    # Uncomment below to run for all stocks
    all_forecasts = scraper.get_company_metrics()
    with open(f'../data/forecast/stock_list_forecasts_{scraper.current_date}.json', 'w') as f:
        json.dump(all_forecasts, f, indent=2)
