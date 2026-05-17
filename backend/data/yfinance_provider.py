# backend/data/yfinance_provider.py
# yfinance 数据提供者 — 基于 yfinance 库获取美股数据

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from backend.data.provider import DataProvider, StockInfo, StockQuote, provider


@provider("yfinance", ["us_stock"], default_priority=0)
class YFinanceProvider(DataProvider):
    """yfinance 数据提供者 — 实现美股的实时行情、K 线、财务数据等接口"""

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        """获取美股实时行情报价"""
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            ticker.history(period="1d")

            # 优先使用 currentPrice，降级到 regularMarketPrice
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)

            return StockQuote(
                symbol=symbol,
                name=info.get("shortName", symbol),
                market="us_stock",
                price=float(price),
                change=float(price - prev_close) if prev_close else 0.0,
                change_pct=float((price - prev_close) / prev_close * 100) if prev_close else 0.0,
                volume=float(info.get("volume", 0)),
                turnover=float(info.get("marketCap", 0)),
                high=float(info.get("dayHigh", 0)),
                low=float(info.get("dayLow", 0)),
                open=float(info.get("open", 0)),
                prev_close=float(prev_close),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get realtime quote for {symbol}: {e}")
            raise

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        """获取美股 K 线历史数据（OHLCV）"""
        import pandas as pd
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            # 周期映射：daily→1d, weekly→1wk, monthly→1mo
            period_map = {"daily": "1d", "weekly": "1wk", "monthly": "1mo"}
            yf_interval = period_map.get(period, "1d")

            df = ticker.history(
                interval=yf_interval,
                start=start_date,
                end=end_date or datetime.now().strftime("%Y-%m-%d"),
            )
            df = df.reset_index()
            # 将英文列名统一为标准格式
            df = df.rename(columns={
                "Date": "date", "Open": "open", "Close": "close",
                "High": "high", "Low": "low", "Volume": "volume",
            })
            # 去除时区信息，统一为 naive datetime
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            return df
        except Exception as e:
            logger.error(f"Failed to get kline for {symbol}: {e}")
            raise

    def get_stock_info(self, symbol: str) -> StockInfo:
        """获取美股基本信息（名称/行业/板块/市值/PE/PB）"""
        import yfinance as yf
        try:
            info = yf.Ticker(symbol).info
            return StockInfo(
                symbol=symbol,
                name=info.get("shortName", symbol),
                market="us_stock",
                industry=info.get("industry", ""),
                sector=info.get("sector", ""),
                market_cap=float(info.get("marketCap", 0)),
                pe_ratio=float(info.get("trailingPE", 0)),
                pb_ratio=float(info.get("priceToBook", 0)),
                dividend_yield=float(info.get("dividendYield", 0) or 0),
            )
        except Exception as e:
            logger.error(f"Failed to get stock info for {symbol}: {e}")
            raise

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        """获取美股财务数据（PE/PB/ROE/营收/利润率/负债率等）"""
        import yfinance as yf
        try:
            info = yf.Ticker(symbol).info
            return {
                "pe_ratio": info.get("trailingPE"),           # 市盈率（TTM）
                "forward_pe": info.get("forwardPE"),          # 预期市盈率
                "pb_ratio": info.get("priceToBook"),          # 市净率
                "ps_ratio": info.get("priceToSalesTrailing12Months"),  # 市销率
                "peg_ratio": info.get("pegRatio"),            # PEG 比率
                "roe": info.get("returnOnEquity"),            # 净资产收益率
                "roa": info.get("returnOnAssets"),            # 总资产收益率
                "revenue": info.get("totalRevenue"),          # 总营收
                "net_income": info.get("netIncomeToCommon"),  # 净利润
                "gross_margin": info.get("grossMargins"),     # 毛利率
                "operating_margin": info.get("operatingMargins"),  # 营业利润率
                "profit_margin": info.get("profitMargins"),   # 净利润率
                "debt_to_equity": info.get("debtToEquity"),   # 资产负债率
                "current_ratio": info.get("currentRatio"),    # 流动比率
                "market_cap": info.get("marketCap"),          # 总市值
                "enterprise_value": info.get("enterpriseValue"),  # 企业价值
                "dividend_yield": info.get("dividendYield"),  # 股息率
                "beta": info.get("beta"),                     # Beta 系数
                "52w_high": info.get("fiftyTwoWeekHigh"),     # 52 周最高价
                "52w_low": info.get("fiftyTwoWeekLow"),       # 52 周最低价
                "50d_avg": info.get("fiftyDayAverage"),       # 50 日均线
                "200d_avg": info.get("twoHundredDayAverage"), # 200 日均线
            }
        except Exception as e:
            logger.error(f"Failed to get financial data for {symbol}: {e}")
            return {}

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        """按关键词搜索美股（yfinance 搜索功能有限）"""
        import yfinance as yf
        try:
            result = yf.Search(keyword)
            quotes = result.quotes or []
            return [
                {"symbol": q.get("symbol", ""), "name": q.get("shortname", ""), "market": "us_stock"}
                for q in quotes[:10]
            ]
        except Exception as e:
            logger.error(f"Failed to search stocks: {e}")
            return []
