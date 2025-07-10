
from utils import fetch_url, parse_html, extract_percentage
import re, json, time, random   
from names import ratio_names, forecast_names

from utils import fetch_url, parse_html, extract_percentage, clean_soup_value
import re, json
from names import ratio_names, forecast_names, STOCK_LIST
from datetime import datetime

# Get the current date and format it as YYYY-MM-DD
# current_date = datetime.now().strftime('%Y-%m-%d')
# print(f"Current date: {current_date}")

class Ratio_Scraper():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_date = datetime.now().strftime('%Y-%m-%d')

    def fetch_data(self, url):
        """Fetch data from the specified URL."""
        response = fetch_url(url, self.headers)
        if not response:
            print(f"Failed to fetch data from {url}")
            return None
        soup = str(parse_html(response.text))
        data = clean_soup_value(soup)
        return data
    
    def extract_all_metrics(self, ticker, data, industry=None):
        """
        Extract all financial metrics from the provided data string.
        """
        # Dictionary to store all metrics
        all_metrics = {"industry": industry}
        
        # Extract values for each ratio name
        for ratio_name in ratio_names:
            pattern = rf'"id":"{ratio_name}","title":"[^"]+","value":"([^"]+)"'
            match = re.search(pattern, data)
            if match:
                # Remove currency symbols and convert to appropriate type if possible
                value = match.group(1)
               
                # if '$' in value:
                value = value.replace('$', '').replace(',', '')
                if value == "n/a":
                    all_metrics[ratio_name] = None
                elif value.endswith('B'):
                    # Convert billion notation to numeric
                    all_metrics[ratio_name] = float(value.replace('B', '')) * 1e9
                elif value.endswith('M'):
                    # Convert million notation to numeric
                    all_metrics[ratio_name] = float(value.replace('M', '')) * 1e6
                elif value.endswith('T'):
                    # Convert trillion notation to numeric
                    all_metrics[ratio_name] = float(value.replace('T', '')) * 1e12
                elif value.endswith('%'):
                    # Convert percentage to decimal
                    all_metrics[ratio_name] = float(value.replace('%', '')) / 100
                elif value.startswith('$'):
                    # Remove dollar sign
                    all_metrics[ratio_name] = value.replace('$', '')
                else:
                    # Keep as is - could be date or other string value
                    all_metrics[ratio_name] = value
            else:
                all_metrics[ratio_name] = None
        
        return all_metrics
    
    def extract_ticker_metrics(self, ticker, industry=None):
        """
        Extract financial metrics for a given ticker symbol.
        
        Args:
            ticker (str): The stock ticker symbol.
        
        Returns:
            dict: A dictionary containing the extracted financial metrics.
        """
        url = f"https://stockanalysis.com/stocks/{ticker}/statistics/"
        data = self.fetch_data(url)
        print("Data fetched successfully for:", ticker)
        # If no data is returned, log the failure and return None
        if not data:
            print(f"Failed to fetch data for {ticker}")
            return None
        # Extract all metrics using the provided ratio names
        return self.extract_all_metrics(ticker, data, industry)
    
    def get_company_metrics(self):
        """
        Get financial metrics for a specific company ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
        
        Returns:
            dict: A dictionary containing the company's financial metrics.
        """
        all_companies_metrics = {}
        for industry, companies in STOCK_LIST.items():
            for company in companies:
                all_companies_metrics[company] = self.extract_ticker_metrics(company, industry)
                time.sleep(random.uniform(10, 30))
        return all_companies_metrics

if __name__ == "__main__":
    ratio_scraper = Ratio_Scraper()
    # print(ratio_scraper.extract_ticker_metrics("NVDA"))  # Example ticker symbol, replace with actual ticker
    all_companies_metrics = (ratio_scraper.get_company_metrics())  # Get metrics for all companies in STOCK_LIST
    with open(f'stock_list_metrics_{ratio_scraper.current_date}.json', 'w') as f:
        json.dump(all_companies_metrics, f, indent=2)
