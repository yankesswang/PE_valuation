from utils import fetch_url, parse_html, extract_percentage, clean_soup_value, clean_json_data
import re
import json
import time
import random
from names import ratio_names, forecast_names
from datetime import datetime
from names import ratio_names, forecast_names, STOCK_LIST

class Forecast_Scraper():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_date = datetime.now().strftime('%Y-%m-%d')
    
    def fetch_stock_data(self, ticker, endpoint="forecast"):
        """Fetch data from StockAnalysis for the given ticker and endpoint."""
        url = f"https://stockanalysis.com/stocks/{ticker}/{endpoint}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = fetch_url(url, headers)
        return (parse_html(response.text)) if response else None

    def parse_annual_data(self, json_string):
        """Parse annual financial data from JSON string."""
        annual_part = json_string.split("annual")[1].split("quarterly")[0][2:-2]
        annual_part = clean_json_data(annual_part)
        return json.loads(annual_part)

    def parse_quarterly_data(self, json_string):
        """Parse quarterly financial data from JSON string."""
        quarterly_part = json_string.split("quarterly")[-1].split("estimatesCharts")[0][2:-4]
        # print(f"Raw quarterly part: {quarterly_part}")  # Debugging output
        quarterly_part = clean_json_data(quarterly_part)
        # print(f"Quarterly part: {quarterly_part}")  # Debugging output
        return json.loads(quarterly_part)

    def create_stock_data_dict(self, annual_data, quarterly_data):
        """Create a structured dictionary from parsed stock data."""
        return {
                'annual': {
                    "current_eps": annual_data['epsThis']['last'] if 'epsThis' in annual_data else None,
                    "current_growth": annual_data['epsThis']['growth'] if 'epsThis' in annual_data else None,
                    "next_year_eps": annual_data['epsNext']['last'] if 'epsNext' in annual_data else None,
                    "next_year_growth": annual_data['epsNext']['growth'] if 'epsNext' in annual_data else None,
                    "current_revenue": annual_data['revenueThis']['last'] if 'revenueThis' in annual_data else None,
                    "current_revenue_growth": annual_data['revenueThis']['growth'] if 'revenueThis' in annual_data else None,
                    "next_year_revenue": annual_data['revenueNext']['last'] if 'revenueNext' in annual_data else None,
                    "next_year_revenue_growth": annual_data['revenueNext']['growth'] if 'revenueNext' in annual_data else None,
                },
                'quarterly': {
                    "eps": quarterly_data['eps'] if 'eps' in quarterly_data else None,
                    "revenue": quarterly_data['revenue'] if 'revenue' in quarterly_data else None,
                    "revenue_growth": quarterly_data['revenueGrowth'] if 'revenue_growth' in quarterly_data else None,
                    "eps_growth": quarterly_data['epsGrowth'] if 'epsGrowth' in quarterly_data else None,
                    # "year": quarterly_data['fiscalYear'] if 'fiscalYear' in quarterly_data else None,
                    # "quarter": quarterly_data['fiscalQuarter'] if 'fiscalQuarter' in quarterly_data else None,
                }
            }
        

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
                print(f"Fetching data for {company}...")
                data = self.fetch_stock_data(company, endpoint="forecast")
                if not data:
                    print(f"Failed to fetch data for {company}")
                    continue
                json_string = clean_soup_value(str(data))
                annual_data = self.parse_annual_data(json_string)
                quarterly_data = self.parse_quarterly_data(json_string)
                all_companies_metrics[company] = self.create_stock_data_dict(annual_data, quarterly_data)
                # 等待，避免被封鎖
                time.sleep(random.uniform(10, 30))
        return all_companies_metrics

# def main():
#     ratio_scraper = Forecast_Scraper()
#     stock_list_forecasts = ratio_scraper.get_company_metrics()
#     with open(f'stock_list_forecasts_{ratio_scraper.current_date}.json', 'w') as f:
#         json.dump(stock_list_forecasts, f, indent=2)
#     # ticker = "NVDA"  # Example ticker symbol
    
    # # For actual web fetching:
    # # soup = fetch_stock_data(ticker)
    # # if soup:
    # #     with open("../data/soup.txt", "w") as f:
    # #         f.write(str(soup))
    
    # # Reading from saved file for testing:
    # with open("../data/soup.txt", "r") as f:
    #     soup_content = f.read()
    
    # json_string = clean_soup_value(soup_content)
    # annual_data = parse_annual_data(json_string)
    # quarterly_data = parse_quarterly_data(json_string)
    
    # result = create_stock_data_dict(ticker, annual_data, quarterly_data)
    # print(result)

# if __name__ == "__main__":
#     main()


