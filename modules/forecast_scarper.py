import pandas as pd
import re, json, json5
import yfinance as yf

# custom imports
from utils import fetch_url, parse_html, extract_percentage
import ast

class StockAnalysisScraper:
    def __init__(self, ticker, current_year = 2025):
        self.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/91.0.4472.124 Safari/537.36'
        }
        self.ticker = ticker
        self.current_year = current_year

    def get_eps_forecast(self):
        """
        Retrieves EPS forecasts for a given company from StockAnalysis.

        Args:
            company (str): The stock ticker symbol.

        Returns:
            dict or None: Dictionary containing EPS for 2024 and 2025, or None if failed.
        """
        url = f"https://stockanalysis.com/stocks/{self.ticker}/forecast/"
        response = fetch_url(url, self.headers)
        if not response:
            return None

        soup = parse_html(response.text)
        table = soup.find('table', {'class': 'w-full whitespace-nowrap border border-gray-200 text-right text-sm dark:border-dark-700 sm:text-base'})
        js_string = str(soup).split('const data')[-1]
        # print(js_string)
        
        js_string = re.sub(r'<[^>]+>', '', js_string)
    
        # Find the array assignment pattern
        # Look for patterns like "= [" or "data = [" 
        array_match = re.search(r'=\s*(\[.*?\]);?\s*(?:Promise|$)', js_string, re.DOTALL)
        
        if not array_match:
            # Try alternative pattern - look for standalone array
            array_match = re.search(r'(\[.*?\]);?\s*(?:Promise|$)', js_string, re.DOTALL)
        
        if not array_match:
            raise ValueError("No JavaScript array found in the string")
        
        array_str = array_match.group(1)
       
       

        if not table:
            print(f"No forecast table found for {self.ticker}")
            return None

        headers_table = [header.get('title', header.text).strip() for header in table.find_all('th')]
        rows = table.find_all('tr')[1:]  # Skip header row
        data = []

        for row in rows:
            cells = row.find_all('td')
            cell_data = [cell.text.strip() for cell in cells]
            # Ensure data aligns with headers
            cell_data += [''] * (len(headers_table) - len(cell_data))
            data.append(cell_data[:len(headers_table)])

        if not data:
            print(f"No forecast data extracted for {self.ticker}")
            return None
    
        df = pd.DataFrame(data, columns=headers_table)
        # print(df)
        # print('====================')
        # print(df.columns)
        # print('====================')
        # print(self.current_year)

        eps_growth = None
        try:
            eps_row = df[df['Fiscal Year'] == 'EPS']
            print(eps_row)

            def _get_eps_value(row, columns, year):
                for col in [str(year), f"FY {year}"]:
                    if col in columns and not row.empty:
                        return float(row[col].values[0])
                return 0.0

            eps_current_year = _get_eps_value(eps_row, df.columns, self.current_year)
            eps_next_year = _get_eps_value(eps_row, df.columns, self.current_year + 1)
            eps_past_year = _get_eps_value(eps_row, df.columns, self.current_year - 1)
            eps_past_year_5 = _get_eps_value(eps_row, df.columns, self.current_year - 5)
            if eps_past_year_5 > 0 and eps_past_year > 0:
                eps_growth = round(((eps_past_year / eps_past_year_5) ** (1 / 5) - 1) * 100, 2) if eps_past_year_5 else None
        
            # print('eps growth:', eps_growth)
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error extracting EPS data for {self.ticker}: {e}")
            eps_current_year, eps_next_year = 0.0, 0.0
        current_year_suffix = str(self.current_year)[-2:]
        next_year_suffix = str(self.current_year + 1)[-2:]
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
            print(soup.prettify())
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
            
            # Verify we found both metrics
            if forecasts['revenue_growth_5y'] is None and forecasts['eps_growth_5y'] is None:
                print(f"No growth forecasts found for {self.ticker}")
    
            return forecasts
            
        except Exception as e:
            print(f"Error extracting growth forecasts: {e}")
            return None
        

    def get_market_cap_and_price(self):
        """
        Retrieves the market capitalization and current price for a given stock ticker.

        Args:
            ticker (str): The stock ticker symbol.

        Returns:
            tuple: A tuple containing the market capitalization and current price, or None if failed.
        """
        try:
            stock = yf.Ticker(self.ticker)
            print(stock.info)
            market_cap = round(int(stock.info['marketCap'])/1000000000, 2) if 'marketCap' in stock.info else "NA"
            current_price = stock.info['currentPrice'] if 'currentPrice' in stock.info else "NA"
            beta_value = stock.info['beta'] if 'beta' in stock.info else "NA"
        
            return {
                'ticker': self.ticker,
                '市值': str(market_cap)+"B",
                '股價': current_price,
                'Beta': (beta_value)
            }
        except Exception as e:
            print(f"Error retrieving data for {self.ticker}: {e}")
            return None


if __name__ == '__main__':
    scraper = StockAnalysisScraper('AAPL', 2025)

    print(scraper.get_growth_forecasts())
    # print(scraper.get_eps_forecast())
    # print(scraper.get_market_cap_and_price())