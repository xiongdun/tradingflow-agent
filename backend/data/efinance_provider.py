# backend/data/efinance_provider.py
# efinance 数据提供者 — AKShare 的备用数据源，同样基于东方财富接口

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from backend.data.provider import DataProvider, StockInfo, StockQuote, bypass_proxy, provider


@provider("efinance", ["a_share", "h_stock"], default_priority=1)
class EFinanceProvider(DataProvider):
    """efinance 数据提供者 — 作为 AKShare 的备用，A 股/港股数据"""

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        import efinance as ef
        try:
            with bypass_proxy():
                df = ef.stock.get_realtime_quotes()
            row = df[df["股票代码"] == symbol]
            if row.empty:
                raise ValueError(f"Stock {symbol} not found")
            r = row.iloc[0]
            return StockQuote(
                symbol=symbol,
                name=str(r.get("股票名称", "")),
                market="a_share",
                price=float(r.get("最新价", 0) or 0),
                change=float(r.get("涨跌额", 0) or 0),
                change_pct=float(r.get("涨跌幅", 0) or 0),
                volume=float(r.get("成交量", 0) or 0),
                turnover=float(r.get("成交额", 0) or 0),
                high=float(r.get("最高", 0) or 0),
                low=float(r.get("最低", 0) or 0),
                open=float(r.get("今开", 0) or 0),
                prev_close=float(r.get("昨收", 0) or 0),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"[efinance] Failed to get realtime quote for {symbol}: {e}")
            raise

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        import efinance as ef
        try:
            period_map = {"daily": 1, "weekly": 2, "monthly": 3}
            klt = period_map.get(period, 1)
            with bypass_proxy():
                df = ef.stock.get_quote_history(symbol, klt=klt, beg=start_date.replace("-", "") if start_date else "20240101", end=end_date.replace("-", "") if end_date else "")
            if df is None or df.empty:
                raise ValueError(f"No kline data for {symbol}")
            df = df.rename(columns={
                "日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume",
                "成交额": "turnover", "振幅": "amplitude",
                "涨跌幅": "change_pct", "涨跌额": "change",
                "换手率": "turnover_rate",
            })
            return df
        except Exception as e:
            logger.error(f"[efinance] Failed to get kline for {symbol}: {e}")
            raise

    def get_stock_info(self, symbol: str) -> StockInfo:
        import efinance as ef
        try:
            with bypass_proxy():
                df = ef.stock.get_realtime_quotes()
            row = df[df["股票代码"] == symbol]
            if row.empty:
                raise ValueError(f"Stock {symbol} not found")
            r = row.iloc[0]
            return StockInfo(
                symbol=symbol,
                name=str(r.get("股票名称", "")),
                market="a_share",
            )
        except Exception as e:
            logger.error(f"[efinance] Failed to get stock info for {symbol}: {e}")
            raise

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        import efinance as ef
        import pandas as pd
        try:
            with bypass_proxy():
                df = ef.stock.get_realtime_quotes()
            row = df[df["股票代码"] == symbol]
            if row.empty:
                return {}
            r = row.iloc[0]
            return {
                "pe_ratio": float(r.get("市盈率-动态", 0) or 0) if pd.notna(r.get("市盈率-动态")) else None,
                "pb_ratio": float(r.get("市净率", 0) or 0) if pd.notna(r.get("市净率")) else None,
                "total_market_cap": float(r.get("总市值", 0) or 0) if pd.notna(r.get("总市值")) else None,
            }
        except Exception as e:
            logger.error(f"[efinance] Failed to get financial data for {symbol}: {e}")
            return {}

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        import efinance as ef
        try:
            with bypass_proxy():
                df = ef.stock.get_realtime_quotes()
            mask = df["股票名称"].str.contains(keyword, na=False) | df["股票代码"].str.contains(keyword, na=False)
            results = df[mask].head(10)
            return [
                {"symbol": str(row["股票代码"]), "name": str(row["股票名称"]), "market": "a_share"}
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"[efinance] Failed to search stocks: {e}")
            return []
