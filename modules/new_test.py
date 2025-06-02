from utils import fetch_url, parse_html, extract_percentage, clean_soup_value, clean_json_data
import re
import json
from names import ratio_names, forecast_names

def fetch_stock_data(ticker, endpoint="forecast"):
    """Fetch data from StockAnalysis for the given ticker and endpoint."""
    url = f"https://stockanalysis.com/stocks/{ticker}/{endpoint}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = fetch_url(url, headers)
    return parse_html(response.text) if response else None

def parse_annual_data(json_string):
    """Parse annual financial data from JSON string."""
    annual_part = json_string.split("annual")[1].split("quarterly")[0][2:-2]
    annual_part = clean_json_data(annual_part)
    return json.loads(annual_part)

def parse_quarterly_data(json_string):
    """Parse quarterly financial data from JSON string."""
    quarterly_part = json_string.split("quarterly")[-1].split("estimatesCharts")[0][2:-4]
    # print(f"Raw quarterly part: {quarterly_part}")  # Debugging output
    quarterly_part = clean_json_data(quarterly_part)
    # print(f"Quarterly part: {quarterly_part}")  # Debugging output
    return json.loads(quarterly_part)

def create_stock_data_dict(ticker, annual_data, quarterly_data):
    """Create a structured dictionary from parsed stock data."""
    return {
        ticker: {
            'annual': {
                "current_eps": annual_data['epsThis']['last'],
                "current_growth": annual_data['epsThis']['growth'],
                "next_year_eps": annual_data['epsNext']['last'],
                "next_year_growth": annual_data['epsNext']['growth'],
                "current_revenue": annual_data['revenueThis']['last'],
                "current_revenue_growth": annual_data['revenueThis']['growth'],
                "next_year_revenue": annual_data['revenueNext']['last'],
                "next_year_revenue_growth": annual_data['revenueNext']['growth'],
            },
            'quarterly': {
                "eps": quarterly_data['eps'],
                "revenue": quarterly_data['revenue'],
                "revenue_growth": quarterly_data['revenueGrowth'],
                "eps_growth": quarterly_data['epsGrowth'],
                "year": quarterly_data['fiscalYear'],
                "quarter": quarterly_data['fiscalQuarter'],
            }
        }
    }

def main():
    ticker = "AAPL"  # Example ticker symbol
    
    # For actual web fetching:
    soup_content = str(fetch_stock_data(ticker))

    try:
        if 'ex:"NASDAQ"' in soup_content:
            split_after_ex = soup_content.split('ex:"NASDAQ"')[1]
            if 'pd:' in split_after_ex:
                json_string = split_after_ex.split('pd:')[1].split(',td')[0].strip('"')
                print(f"Extracted JSON string: {json_string}")  # Debugging output
            else:
                json_string = "No pricing data found"
        else:
            json_string = "NASDAQ exchange marker not found"
    except Exception as e:
        json_string = f"Error parsing data: {str(e)}" 

if __name__ == "__main__":
    main()