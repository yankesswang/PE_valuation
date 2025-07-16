import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import time, random
from requests.exceptions import RequestException
from tqdm import tqdm 
import requests
from bs4 import BeautifulSoup
import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from requests.exceptions import RequestException, HTTPError
import pandas as pd
import random, json
from datetime import datetime

# custom imports
from utils import fetch_url, parse_html, compute_iqr_statistics, filter_outliers
from names import STOCK_LIST, PE_TICKER_TO_COMPANY

class PERatioScraper:
    def __init__(self):
        self.current_date = datetime.now().strftime('%Y-%m-%d')

    def parse_pe_ratios(self, ticker: str) -> List[float]:
        """
        Parse PE ratios from the given HTML content.

        Args:
            html_content (str): HTML content of the webpage.

        Returns:
            List[float]: List of PE ratios extracted.
        """
        company = PE_TICKER_TO_COMPANY.get(ticker.lower())
        url = f"https://www.macrotrends.net/stocks/charts/{ticker.upper()}/{company}/pe-ratio"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        try:
            response = fetch_url(url, headers)
            if not response:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find("table", class_="table")

            if not table:
                print("PE ratio table not found in the HTML content.")
                return []

            rows = table.find("tbody").find_all("tr")
            pe_ratios = []

            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    pe_ratio_str = cells[3].get_text(strip=True)
                    # Handle cases like 'N/A' or empty strings
                    try:
                        pe_ratio = float(pe_ratio_str.replace(",", ""))
                        pe_ratios.append(pe_ratio)
                    except ValueError:
                        # Skip invalid PE ratio values
                        continue
            return pe_ratios
        except Exception as e:
            print(f"Error extracting growth forecasts: {e}")
            return None

    def analyze_pe_ratios(self, pe_ratios: List[float], num_latest: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """
        Analyze PE ratios by computing mean before and after outlier removal.

        Args:
            pe_ratios (List[float]): List of PE ratios.
            num_latest (int): Number of latest PE ratios to consider.

        Returns:
            Tuple[Optional[float], Optional[float]]: Mean PE after outlier removal and original mean.
        """
        if not pe_ratios:
            return None, None
        # Remove zeros from the PE ratios array
        pe_ratios = [pe for pe in pe_ratios if pe != 0]
        if not pe_ratios:
            return None
        # Consider the latest `num_latest` PE ratios
        latest_pe_ratios = pe_ratios[:num_latest]
        pe_array = np.array(latest_pe_ratios)

        # Compute IQR statistics
        q1, q3, iqr = compute_iqr_statistics(pe_array)
        filtered_pe = filter_outliers(pe_array, q1, q3, iqr)

        # Compute means
        if filtered_pe.size > 0:
            median_filtered_pe = round(np.median(filtered_pe), 1)
            return median_filtered_pe
        else:
            return 0
        

    def get_company_metrics(self):
        """
        Get financial metrics for a specific company ticker.
        
        Args:
            ticker (str): The stock ticker symbol.
        
        Returns:
            dict: A dictionary containing the company's financial metrics.
        """
        all_companies_metrics = {}
        # with open("/Users/yankesswang/Projects/PE_valuation/data/stock_list_PE_2025-06-29.json", 'r') as f:
        #     pe_dict = json.load(f)
        for industry, companies in STOCK_LIST.items():
            for company in companies:
                # if company in pe_dict:
                #     print(f"Skipping {company}, already processed.")
                #     all_companies_metrics[company] = pe_dict[company]
                #     continue
                time.sleep(random.uniform(10, 30))
                pe_ratios = self.parse_pe_ratios(company)
                if not pe_ratios:
                    print(f"Failed to fetch PE ratios for {company}")
                    continue
                # Analyze PE ratios
                print("Analyzing PE ratios for:", company)
                print(f"PE ratios fetched for {company}: {pe_ratios}")
                pe_median = self.analyze_pe_ratios(pe_ratios)
                if pe_median is None:
                    print(f"Failed to analyze PE ratios for {company}")
                    continue

                # Store the metrics
                print(f"Fetched and analyzed PE ratios for {company}: {pe_median}")

                # Store the company metrics
                all_companies_metrics[company] = pe_median

                time.sleep(random.uniform(10, 30))
        return all_companies_metrics

if __name__ == "__main__":


    pe_scraper = PERatioScraper()
    # ticker = 'BA'
    # pe_data = pe_scraper.parse_pe_ratios(ticker)

    # print(f"PE Ratios for {ticker}:", pe_data)
    # pe_median = pe_scraper.analyze_pe_ratios(pe_data)
    # print(f"Median PE Ratio for {ticker}:", pe_median)

    pe_data = pe_scraper.get_company_metrics()
    with open(f'../data/pe/stock_list_PE_{pe_scraper.current_date}.json', 'w') as f:
        json.dump(pe_data, f, indent=2)