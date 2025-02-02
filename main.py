# example_usage.py

from modules.pe_scraper import get_pe_ratio

def main():
    stock_symbol = "AAPL"  # Example: Apple Inc.
    pe_ratio = get_pe_ratio(stock_symbol)
    
    if pe_ratio is not None:
        print(f"The 5-year average PE ratio for {stock_symbol} is {pe_ratio}.")
    else:
        print(f"Failed to retrieve the PE ratio for {stock_symbol}.")

if __name__ == "__main__":
    main()
