# backend/data/baostock_provider.py
# baostock 数据提供者 — 基于证券宝的 A 股数据（不依赖东方财富）

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from loguru import logger

from backend.data.provider import DataProvider, StockInfo, StockQuote, provider


def _to_bs_code(symbol: str) -> str:
    """将股票代码转换为 baostock 格式（sh.600519 / sz.000001）"""
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith(("6", "9")):
        return f"sh.{symbol}"
    return f"sz.{symbol}"


@provider("baostock", ["a_share"], default_priority=2)
class BaostockProvider(DataProvider):
    """baostock 数据提供者 — A 股历史数据，不经过东方财富"""

    def _login(self):
        import baostock as bs
        lg = bs.login()
        if lg.error_code != "0":
            raise ConnectionError(f"baostock login failed: {lg.error_msg}")
        return bs

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        raise NotImplementedError("baostock 不支持实时行情")

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        bs = self._login()
        try:
            freq_map = {"daily": "d", "weekly": "w", "monthly": "m"}
            freq = freq_map.get(period, "d")
            code = _to_bs_code(symbol)
            start = start_date or "2024-01-01"
            end = end_date or datetime.now().strftime("%Y-%m-%d")

            rs = bs.query_history_k_data_plus(
                code, "date,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start, end_date=end, frequency=freq, adjustflag="2",
            )
            if rs.error_code != "0":
                raise ValueError(f"baostock query failed: {rs.error_msg}")

            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())

            if not rows:
                raise ValueError(f"No data for {symbol}")

            df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume", "turnover", "turnover_rate", "change_pct"])
            for col in ["open", "high", "low", "close", "volume", "turnover", "turnover_rate", "change_pct"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        finally:
            bs.logout()

    def get_stock_info(self, symbol: str) -> StockInfo:
        bs = self._login()
        try:
            code = _to_bs_code(symbol)
            rs = bs.query_stock_basic(code=code)
            if rs.error_code != "0" or not rs.next():
                raise ValueError(f"Stock {symbol} not found")
            row = rs.get_row_data()
            return StockInfo(
                symbol=symbol,
                name=row[1] if len(row) > 1 else "",
                market="a_share",
            )
        finally:
            bs.logout()

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError("baostock 财务数据需额外查询")

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        raise NotImplementedError("baostock 不支持股票搜索")
