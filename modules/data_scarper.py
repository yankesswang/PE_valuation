import pandas as pd
import re, json
import yfinance as yf

# custom imports
from utils import fetch_url, parse_html, extract_percentage
import ast
from datetime import datetime

class StockAnalysisScraper:
    def __init__(self, ticker, current_year = 2025):
        self.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/91.0.4472.124 Safari/537.36'
        }
        self.ticker = ticker
        self.current_year = current_year
        date = datetime.now().strftime('%Y-%m-%d')
        with open(f"../data/ratio/stock_list_ratio_{date}.json", "r") as f:
            self.ratio_data = json.load(f)

        with open(f"../data/forecast/stock_list_forecasts_{date}.json", "r") as f:
            self.forecast_data = json.load(f)

        with open(f"../data/pe/stock_list_PE_{date}.json", "r") as f:
            self.pe_data = json.load(f)
            
    def get_eps_forecast(self):
        """
        Retrieves EPS forecasts for a given company from StockAnalysis.

        Args:
            company (str): The stock ticker symbol.

        Returns:
            dict or None: Dictionary containing EPS for 2024 and 2025, or None if failed.
        """
        current_year_suffix = str(self.current_year)[-2:]
        next_year_suffix = str(self.current_year + 1)[-2:]
        annual_data = (self.forecast_data[self.ticker]["annual"])
        quarterly_growth_data = (self.forecast_data[self.ticker]["quarterly"].get("eps_growth", None))
       
        eps_current_year = round(annual_data.get("current_eps", None), 2)
        eps_next_year = round(annual_data.get("next_year_eps", None), 2)
        
        valid_values = [x for x in quarterly_growth_data[:min(5, len(quarterly_growth_data))] if x is not None] if quarterly_growth_data else []
        eps_growth = round(sum(valid_values) / len(valid_values), 2) if valid_values else None
        return {
            f"eps_{current_year_suffix}" : eps_current_year,
            f"eps_{next_year_suffix}" : eps_next_year,
            "past_eps_growth" : eps_growth
        }

    def get_growth_forecasts(self):
        """
        Retrieves 5-year growth forecasts from StockAnalysis.com.
        
        Args:
            company (str): The stock ticker symbol
            
        Returns:
            dict or None: Dictionary containing revenue and EPS growth forecasts
        """
        url = f"https://stockanalysis.com/stocks/{self.ticker}/statistics/"

        try:
            response = fetch_url(url,self.headers)
            if not response:
                return None
                
            soup = parse_html(response.text)
            
            # Find growth forecast values
            forecasts = {
                'revenue_growth_5y': None,
                'eps_growth_5y': None
            }
          
            # Find elements containing the forecasts
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if not cells:
                    continue
                    
                label_cell = cells[0].get_text(strip=True)
                if 'Revenue Growth Forecast' in label_cell and '5Y' in label_cell:
                    forecasts['revenue_growth_5y'] = extract_percentage(cells[-1].get_text(strip=True))
                elif 'EPS Growth Forecast' in label_cell and '5Y' in label_cell:
                    forecasts['eps_growth_5y'] = extract_percentage(cells[-1].get_text(strip=True))

            if forecasts['revenue_growth_5y'] is None and forecasts['eps_growth_5y'] is None:
                print(f"No growth forecasts found for {self.ticker}")
    
            return forecasts
            
        except Exception as e:
            print(f"Error extracting growth forecasts: {e}")
            return None
    
    def fetch_stock_data(self, ticker, endpoint="forecast"):
        """Fetch data from StockAnalysis for the given ticker and endpoint."""
        url = f"https://stockanalysis.com/stocks/{ticker}/{endpoint}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = fetch_url(url, headers)
        return (parse_html(response.text)) if response else None
    
    def get_price(self, ticker):
        soup_content = str(self.fetch_stock_data(ticker))

        try:
            if 'ex:"NASDAQ"' in soup_content:
                split_after_ex = soup_content.split('ex:"NASDAQ"')[1]
                if 'pd:' in split_after_ex:
                    stock_price= split_after_ex.split('pd:')[1].split(',td')[0].strip('"')
                    print(f"Extracted stock price: {stock_price}")  # Debugging output
                    return float(stock_price)
                else:
                    return 0.0
            else:
                return 0.0
        except Exception as e:
            return f"Error parsing data: {str(e)}" 

    def get_market_cap_and_price(self):
        """
        Retrieves the market capitalization and current price for a given stock ticker.

        Args:
            ticker (str): The stock ticker symbol.

        Returns:
            tuple: A tuple containing the market capitalization and current price, or None if failed.
        """
        # try:
            # stock = yf.Ticker(self.ticker)
       

        market_cap = round(self.ratio_data[self.ticker]["marketcap"]/1000000000.0, 2) 
        # stock_price = self.get_price(self.ticker)
        stock_price = yf.Ticker(self.ticker).info["regularMarketPrice"]
        beta_value = self.ratio_data[self.ticker]["beta"]
    
        return {
            'ticker': self.ticker,
            '市值': str(market_cap)+"B",
            '股價': stock_price,
            'Beta': (beta_value)
        }
        # except Exception as e:
        #     print(f"Error retrieving data for {self.ticker}: {e}")
        #     return None


if __name__ == '__main__':
    scraper = StockAnalysisScraper('AMZN', 2025)

    print(scraper.get_growth_forecasts())
    print(scraper.get_market_cap_and_price())