import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import time, random
from requests.exceptions import RequestException
from tqdm import tqdm  # Optional: For progress bars
import requests
from bs4 import BeautifulSoup
import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from requests.exceptions import RequestException, HTTPError
import pandas as pd
from tqdm import tqdm
import random

# custom imports
from utils import fetch_url, parse_html, compute_iqr_statistics, filter_outliers

TICKER_TO_COMPANY: Dict[str, str] = {
    # 大科技
    "goog": "alphabet",
    "meta": "meta-platforms",
    "amzn": "amazon",
    "nflx": "netflix",
    "aapl": "apple",
    "msft": "microsoft",
    "tsla": "tesla",
    "adbe": "adobe",

    # 航空郵輪
    "aal": "american-airlines",
    "luv": "southwest-airlines",
    "dal": "delta-air-lines",
    "ual": "united-airlines",
    "alk": "alaska-air-group",
    "ba": "boeing",
    "eadsy": "airbus",
    "ccl": "carnival",
    "rcl": "royal-caribbean",

    # 銀行
    "bac": "bank-of-america",
    "jpm": "jpmorgan-chase",
    "gs": "goldman-sachs",
    "c": "citigroup",
    "wfc": "wells-fargo",
    "blk": "blackrock",
    "nu": "nu-holdings",
    "sofi": "sofi",

    # 傳統
    "dis": "walt-disney",
    "isrg": "intuitive-surgical",
    "unh": "unitedhealth-group",
    "abbv": "abbvie",
    "cvs": "cvs-health",
    "trv": "the-travelers-companies",

    # 支付
    "ma": "mastercard",
    "v": "visa",
    "pypl": "paypal",
    "axp": "american-express",

    # 零售
    "lulu": "lululemon-athletica",
    "gps": "gap",
    "cost": "costco-wholesale",
    "pg": "procter-&-gamble",
    "kr": "kroger",
    "jwn": "nordstrom",
    "nke": "nike",
    "dg": "dollar-general",
    "fl": "foot-locker",
    "lvmhf": "lvmh",
    "el": "estée-lauder",
    "pvh": "pvh-corp.",
    "tpr": "tapestry",

    # 食品
    "tsn": "tyson-foods",
    "mcd": "mcdonald's",
    "sbux": "starbucks",
    "ko": "coca-cola",
    "pep": "pepsi-co",
    "cmg": "chipotle-mexican-grill",
    "yum": "yum!-brands",
    "dpz": "domino's-pizza",
    "cake": "the-cheesecake-factory",
    "jack": "jack-in-the-box",
    "play": "dave-&-busters",
    "fizz": "national-beverage",
    "blmn": "bloomin'-brands",
    "denn": "denny's",
    "din": "dine-brands-global",

    # 半導體
    "nvda": "nvidia",
    "tsm": "taiwan-semiconductor-(tsmc)",
    "amd": "advanced-micro-devices",
    "qcom": "qualcomm",
    "mu": "micron-technology",
    "intc": "intel",
    "asml": "asml-holding",
    "swks": "skyworks-solutions",
    "qrvo": "qorvo",
    "avgo": "broadcom",
    "amat": "applied-materials",
    "mrvl": "marvell-technology",
    "arm": "arm-holdings",
    "cls": "celestica",
    "dell": "dell-technologies",
    "hpe": "hewlett-packard-enterprise",

    # 原油
    "cvx": "chevron",
    "vlo": "valero-energy",
    "cop": "conocophillips",
    "xom": "exxon-mobil",
    "oxy": "occidental-petroleum",
    "cpe": "callon-petroleum",
    "enb": "enbridge",

    # 旅遊
    "bkng": "booking-holdings",
    "expe": "expedia-group",
    "mar": "marriott-international",
    "hlt": "hilton-worldwide",
    "abnb": "airbnb",
    "h": "hyatt-hotels",
    "wynn": "wynn-resorts",
    "ihg": "intercontinental-hotels",
    "lvs": "las-vegas-sands",
    "mgm": "mgm-resorts",

    # 工業
    "nee": "nextera-energy",
    "de": "deere-&-company",
    "hd": "home-depot",
    "apd": "air-products-&-chemicals",
    "cat": "caterpillar",
    "etn": "eaton-corporation",
    "hon": "honeywell",
    "wm": "waste-management",
    "ge": "general-electric",
    "mmm": "3m-company",
    "sum": "summit-materials",
    "x": "u.s.-steel",
    "enph": "enphase-energy",
    "sedg": "solaredge",
    "fslr": "first-solar",

    # SaaS
    "sap": "sap-se",           # Ticker is sometimes just 'sap'
    "cflt": "confluent",
    "acn": "accenture",
    "bsx": "boston-scientific",
    "shop": "shopify",
    "crm": "salesforce",
    "ddog": "datadog",
    "now": "servicenow",
    "intu": "intuit",
    "sq": "block-(square)",
    "wdays": "workday",
    "snow": "snowflake",
    "mdb": "mongodb",
    "okta": "okta",
    "adsk": "autodesk",
    "ttd": "the-trade-desk",
}

# -------------------------------
# Statistical Computations
# -------------------------------



def parse_pe_ratios(ticker: str) -> List[float]:
    """
    Parse PE ratios from the given HTML content.

    Args:
        html_content (str): HTML content of the webpage.

    Returns:
        List[float]: List of PE ratios extracted.
    """
    company = TICKER_TO_COMPANY.get(ticker.lower())
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

def analyze_pe_ratios(pe_ratios: List[float], num_latest: int = 20) -> Tuple[Optional[float], Optional[float]]:
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