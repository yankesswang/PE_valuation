import time
import random
from tqdm import tqdm
import pandas as pd
from datetime import date
import json

# custom imports
from data_scarper import StockAnalysisScraper
from names import STOCK_LIST

class Valuation_Analyzer:
    def __init__(self, current_year):
        # We only store the current_year in the constructor
        # The ticker will be handled in process_company(ticker)
        self.current_year = current_year

    def calculate_valuations(self, stock_data, pe_median):
        """
        Calculates various valuations and differences based on stock data.
        
        Args:
            stock_data (dict): Contains 'eps_20xx', '市值', '股價', 'eps_growth_5y', etc.
            pe_median (float): The five-year median PE ratio.
        
        Returns:
            dict: Calculated valuations and differences.
        """
        valuations = {}
        # print(stock_data)
        # Derive suffixes
        current_year_suffix = str(self.current_year)[-2:]
        next_year_suffix = str(self.current_year + 1)[-2:]

        # Growth-based "預估PE"
        growth = stock_data.get('eps_growth_5y', 0) or 0
        valuations['預估PE'] = growth
        
        if 0 < growth < 5:
            valuations['預估PE'] *= 0.8
        elif 5 <= growth < 10:
            valuations['預估PE'] *= 1.0
        elif 10 <= growth < 15:
            valuations['預估PE'] *= 1.1
        elif 15 <= growth < 20:
            valuations['預估PE'] *= 1.2
        elif 20 <= growth < 30:
            valuations['預估PE'] *= 1.5
        else:
            valuations['預估PE'] *= 2.0
        
        valuations['預估PE'] = round(valuations['預估PE'], 2) if valuations['預估PE'] else 0.0

        # Calculate EPS and "合理價" for current year
        valuations[f"{current_year_suffix}年EPS"] = stock_data.get(f'eps_{current_year_suffix}', 0.0)
        valuations[f"{current_year_suffix}年合理價"] = round(
            valuations[f"{current_year_suffix}年EPS"] * valuations['預估PE']
        )

        # Calculate EPS and "合理價" for next year
        valuations[f"{next_year_suffix}年EPS"] = stock_data.get(f'eps_{next_year_suffix}', 0.0)
        valuations[f"{next_year_suffix}年合理價"] = round(
            valuations[f"{next_year_suffix}年EPS"] * valuations['預估PE']
        )

        # Five-year PE Median and Median Valuation
        valuations["五年PE MEDIAN"] = pe_median
        valuations["五年PE中位價"] = round(pe_median * valuations[f"{current_year_suffix}年EPS"])

        # Valuation Comparison for current year
        current_price = stock_data.get('股價', 0)
        if current_price > valuations["五年PE中位價"]:
            valuations[f"{current_year_suffix}年估值"] = "高估"
        else:
            valuations[f"{current_year_suffix}年估值"] = "低估"

        if valuations["五年PE中位價"] != 0:
            diff_pct = (valuations['五年PE中位價'] - current_price) / valuations['五年PE中位價'] * 100
            valuations[f"{current_year_suffix}年相差百分比"] = f"{round(diff_pct)}%"
        else:
            valuations[f"{current_year_suffix}年相差百分比"] = "N/A"

        # Five-year PE Median Valuation for Next Year
        valuations[f"{next_year_suffix}年PE中位價"] = round(pe_median * valuations[f"{next_year_suffix}年EPS"])

        # Valuation Comparison for next year
        if current_price > valuations[f"{next_year_suffix}年PE中位價"]:
            valuations[f"{next_year_suffix}年估值"] = "高估"
        else:
            valuations[f"{next_year_suffix}年估值"] = "低估"

        if valuations[f"{next_year_suffix}年PE中位價"] != 0:
            diff_pct = (valuations[f"{next_year_suffix}年PE中位價"] - current_price) / valuations[f"{next_year_suffix}年PE中位價"] * 100
            valuations[f"{next_year_suffix}年相差百分比"] = f"{round(diff_pct)}%"
        else:
            valuations[f"{next_year_suffix}年相差百分比"] = "N/A"

        return valuations

    def process_company(self, ticker):
        """
        Processes data for a single company.
        
        Args:
            ticker (str): The stock ticker symbol.

        Returns:
            dict or None: Dictionary containing all required data, or None if failed.
        """
        # Create a local scraper for this ticker
        # print(f"\n正在處理公司 in process company：{ticker}")
        stock_analysis = StockAnalysisScraper(ticker, self.current_year)
        eps_forecast = stock_analysis.get_eps_forecast()
        print("eps_forecast: ",eps_forecast)
        # Growth data
        growth_data = stock_analysis.get_growth_forecasts()
        
        pe_data = stock_analysis.pe_data
        
        if ticker not in pe_data:
            print(f"Ticker {ticker} not found in PE data.")
            return None
        pe_median = pe_data.get(ticker, 0.0)
        
        # Market cap, price, etc.
        stock_data = stock_analysis.get_market_cap_and_price()
        if not stock_data:
            return None

        # Combine all data into one dict
        stock_data.update(eps_forecast)
        stock_data.update(growth_data)

        # Perform valuation calculations
        valuations = self.calculate_valuations(stock_data, pe_median)

        # Suffixes for columns
        current_year_suffix = str(self.current_year)[-2:]
        next_year_suffix = str(self.current_year + 1)[-2:]

        # Build final result for this ticker
        company_data = {
            "Revenue Growth Forecast (5Y)": str(stock_data.get("revenue_growth_5y", 0))+"%",
            "EPS Growth Forecast (5Y)": str(stock_data.get("eps_growth_5y", 0))+"%",
            "EPS Growth Past 5 Years": str(stock_data.get("past_eps_growth", 0))+"%",
            "預估PE": valuations.get("預估PE", 0),
            f"{current_year_suffix}年EPS": valuations.get(f"{current_year_suffix}年EPS", 0),
            f"{current_year_suffix}年合理價": valuations.get(f"{current_year_suffix}年合理價", 0),
            f"{next_year_suffix}年EPS": valuations.get(f"{next_year_suffix}年EPS", 0),
            f"{next_year_suffix}年合理價": valuations.get(f"{next_year_suffix}年合理價", 0),
            "五年PEMEDIAN": valuations.get("五年PE MEDIAN", 0),
            "五年PE中位價": valuations.get("五年PE中位價", 0),
            "市值": stock_data.get("市值", "N/A"),
            "股價": stock_data.get("股價", 0),
            f"{current_year_suffix}年估值": valuations.get(f"{current_year_suffix}年估值", "N/A"),
            f"{current_year_suffix}年相差百分比": valuations.get(f"{current_year_suffix}年相差百分比", "N/A"),
            f"{next_year_suffix}年PE中位價": valuations.get(f"{next_year_suffix}年PE中位價", 0),
            f"{next_year_suffix}年估值": valuations.get(f"{next_year_suffix}年估值", "N/A"),
            f"{next_year_suffix}年相差百分比": valuations.get(f"{next_year_suffix}年相差百分比", "N/A"),
        }

        return company_data

    def aggregate_company_data(self):
        """
        將所有公司的數據聚合成一個字典，每個產業對應一個轉置後的DataFrame。
        
        Returns:
            dict: 以產業為鍵，轉置後的DataFrame為值的字典。
        """
        industry_dataframes = {}

        for industry, companies in STOCK_LIST.items():
            print(f"\n正在處理產業：{industry}，包含 {len(companies)} 家公司。")
            all_companies_data = []
            
            for company in tqdm(companies, desc=f"處理 {industry}", unit="公司"):
                print(f"正在處理公司：{company}")
                
                # Directly call process_company for each ticker
                company_data = self.process_company(company)
                
                if company_data:
                    # Add metadata
                    company_data['Industry'] = industry
                    company_data['Company'] = company
                    all_companies_data.append(company_data)
                else:
                    print(f"{company} 的數據處理失敗。")
                
                # 等待，避免被封鎖
                time.sleep(random.uniform(10, 30))
                
            if all_companies_data:
                # Create DataFrame
                df = pd.DataFrame(all_companies_data)
                # Move Industry & Company to the front
                df.insert(0, 'Industry', df.pop('Industry'))
                df.insert(1, 'Company', df.pop('Company'))
                # Transpose (pivot) the DataFrame
                df_transposed = df.set_index(['Industry', 'Company']).transpose()
                # Save to dict
                industry_dataframes[industry] = df_transposed
            else:
                print(f"{industry} 沒有可用的公司數據。")
        return industry_dataframes

    def save_to_excel(self, industry_dataframes, path):
        """
        將各產業的DataFrame保存到Excel文件中的不同工作表，並轉置數據。

        Args:
            industry_dataframes (dict): 以產業為鍵，轉置後的DataFrame為值的字典。
            path (str): 要保存的Excel文件路徑。
        """
        with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
            for industry, df in industry_dataframes.items():
                df.to_excel(writer, sheet_name=industry, index=True)
        print(f"\n所有數據已保存到 {path}")


if __name__ == "__main__":
    analyzer = Valuation_Analyzer(2025)
    # res = analyzer.process_company('ADBE')
    # print(res)

    # Gather the data for all industries/companies
    df_dict = analyzer.aggregate_company_data()
    
    # Save results to Excel
    analyzer.save_to_excel(df_dict, f'../valuation/stock_data_{date.today()}.xlsx')
