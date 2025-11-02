from utils import fetch_url, parse_html
import re, json, time, random
from datetime import datetime
from names import STOCK_LIST

class Forecast_Scraper_Fixed():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_date = datetime.now().strftime('%Y-%m-%d')

    def parse_value(self, value_str):
        """Parse a value string from the website into a numeric value"""
        if not value_str or value_str == 'n/a' or value_str == '-' or value_str == 'N/A':
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
            return value_str  # Return as string if can't convert

    def extract_forecast_data(self, ticker):
        """
        Extract EPS and Revenue forecast data for a given ticker from the forecast page.
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

        # Find all tables on the page
        tables = soup.find_all('table')

        # Parse annual forecast table (usually the first table)
        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) < 2:
                    continue

                label = cells[0].get_text(strip=True)

                # Check for EPS row
                if 'EPS' in label and 'Diluted' in label:
                    # Get current year and next year values
                    if len(cells) >= 3:
                        current_year_val = cells[-2].get('title') or cells[-2].get_text(strip=True)
                        next_year_val = cells[-1].get('title') or cells[-1].get_text(strip=True)
                        forecast_data['annual']['current_eps'] = self.parse_value(current_year_val)
                        forecast_data['annual']['next_year_eps'] = self.parse_value(next_year_val)

                # Check for Revenue row
                elif 'Revenue' in label and 'Growth' not in label:
                    if len(cells) >= 3:
                        current_year_val = cells[-2].get('title') or cells[-2].get_text(strip=True)
                        next_year_val = cells[-1].get('title') or cells[-1].get_text(strip=True)
                        forecast_data['annual']['current_revenue'] = self.parse_value(current_year_val)
                        forecast_data['annual']['next_year_revenue'] = self.parse_value(next_year_val)

                # Check for EPS Growth
                elif 'EPS Growth' in label:
                    if len(cells) >= 3:
                        current_growth = cells[-2].get('title') or cells[-2].get_text(strip=True)
                        next_growth = cells[-1].get('title') or cells[-1].get_text(strip=True)
                        forecast_data['annual']['current_growth'] = self.parse_value(current_growth)
                        forecast_data['annual']['next_year_growth'] = self.parse_value(next_growth)

                # Check for Revenue Growth
                elif 'Revenue Growth' in label:
                    if len(cells) >= 3:
                        current_growth = cells[-2].get('title') or cells[-2].get_text(strip=True)
                        next_growth = cells[-1].get('title') or cells[-1].get_text(strip=True)
                        forecast_data['annual']['current_revenue_growth'] = self.parse_value(current_growth)
                        forecast_data['annual']['next_year_revenue_growth'] = self.parse_value(next_growth)

        # Try to extract quarterly data from tables
        # Look for tables with quarterly data (Q1, Q2, Q3, Q4 headers)
        for table in tables:
            header_row = table.find('thead')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
                # Check if this is a quarterly table
                if any('Q' in h or 'Quarter' in h for h in headers):
                    body_rows = table.find('tbody').find_all('tr') if table.find('tbody') else []
                    for row in body_rows:
                        cells = row.find_all('td')
                        if not cells:
                            continue

                        label = cells[0].get_text(strip=True)
                        values = [self.parse_value(cell.get('title') or cell.get_text(strip=True))
                                for cell in cells[1:]]

                        if 'EPS' in label and 'Growth' not in label:
                            forecast_data['quarterly']['eps'] = values
                        elif 'EPS Growth' in label:
                            forecast_data['quarterly']['eps_growth'] = values
                        elif 'Revenue' in label and 'Growth' not in label:
                            forecast_data['quarterly']['revenue'] = values
                        elif 'Revenue Growth' in label:
                            forecast_data['quarterly']['revenue_growth'] = values

        print(f"Extracted forecast data for {ticker}")
        return forecast_data

    def get_company_metrics(self):
        """Get forecast metrics for all companies in STOCK_LIST"""
        all_companies_forecasts = {}
        for industry, companies in STOCK_LIST.items():
            for company in companies:
                print(f"Fetching forecast data for {company}...")
                forecast = self.extract_forecast_data(company)
                if forecast:
                    all_companies_forecasts[company] = forecast
                # Wait to avoid rate limiting
                time.sleep(random.uniform(10, 30))
        return all_companies_forecasts

if __name__ == "__main__":
    scraper = Forecast_Scraper_Fixed()

    # Test with a single stock first
    print("Testing with NVDA...")
    test_result = scraper.extract_forecast_data("NVDA")
    print(f"\\nTest result for NVDA:")
    print(json.dumps(test_result, indent=2))

    # Uncomment below to run for all stocks
    all_forecasts = scraper.get_company_metrics()
    with open(f'../data/forecast/stock_list_forecasts_{scraper.current_date}.json', 'w') as f:
        json.dump(all_forecasts, f, indent=2)
