# backend/data/futures_provider.py
# 期货数据提供者 — 基于 AKShare 获取国内/国际期货数据

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from backend.data.provider import DataProvider, StockInfo, StockQuote, bypass_proxy, provider


def _find_col(row, candidates: list[str], default: str = "") -> str:
    """从候选列名中找到实际存在的列"""
    if row is None:
        return default
    for name in candidates:
        if name in row.index:
            return name
    return default


@provider("akshare", ["futures"], default_priority=0)
class FuturesProvider(DataProvider):
    """期货数据提供者 — 实现期货合约的实时行情、K 线、基本信息等接口"""

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        """获取期货合约实时行情报价"""
        import akshare as ak
        import pandas as pd
        try:
            variety = "".join(c for c in symbol if c.isalpha())
            with bypass_proxy():
                df = ak.futures_zh_realtime(symbol=variety)
            if df.empty:
                raise ValueError(f"Futures {symbol} not found")
            code_col = df.columns[0]
            row = df[df[code_col].astype(str).str.contains(symbol, case=False, na=False)]
            if row.empty:
                row = df.head(1)
            r = row.iloc[0]
            name_c = _find_col(r, ["名称", "品种", "合约"], symbol)
            price_c = _find_col(r, ["最新价", "现价"])
            change_c = _find_col(r, ["涨跌额", "涨跌"])
            chg_pct_c = _find_col(r, ["涨跌幅"])
            vol_c = _find_col(r, ["成交量"])
            turn_c = _find_col(r, ["成交额"])
            hi_c = _find_col(r, ["最高"])
            lo_c = _find_col(r, ["最低"])
            opn_c = _find_col(r, ["今开", "开盘"])
            prev_c = _find_col(r, ["昨收", "昨结"])

            def _float(val):
                return float(val) if pd.notna(val) else 0.0

            return StockQuote(
                symbol=symbol, name=str(r[name_c]) if name_c else symbol, market="futures",
                price=_float(r.get(price_c, 0)) if price_c else 0.0,
                change=_float(r.get(change_c, 0)) if change_c else 0.0,
                change_pct=_float(r.get(chg_pct_c, 0)) if chg_pct_c else 0.0,
                volume=_float(r.get(vol_c, 0)) if vol_c else 0.0,
                turnover=_float(r.get(turn_c, 0)) if turn_c else 0.0,
                high=_float(r.get(hi_c, 0)) if hi_c else 0.0,
                low=_float(r.get(lo_c, 0)) if lo_c else 0.0,
                open=_float(r.get(opn_c, 0)) if opn_c else 0.0,
                prev_close=_float(r.get(prev_c, 0)) if prev_c else 0.0,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get futures realtime quote for {symbol}: {e}")
            raise

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        """获取期货 K 线历史数据"""
        import pandas as pd
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.futures_zh_daily_sina(symbol=symbol)
            if df.empty:
                return pd.DataFrame()
            col_map = {}
            for col in df.columns:
                cl = col.lower()
                if "日期" in col or "date" in cl:
                    col_map[col] = "date"
                elif "开盘" in col or "open" in cl:
                    col_map[col] = "open"
                elif "收盘" in col or "close" in cl:
                    col_map[col] = "close"
                elif "最高" in col or "high" in cl:
                    col_map[col] = "high"
                elif "最低" in col or "low" in cl:
                    col_map[col] = "low"
                elif "成交量" in col or "volume" in cl:
                    col_map[col] = "volume"
            if col_map:
                df = df.rename(columns=col_map)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                if start_date:
                    df = df[df["date"] >= start_date]
                if end_date:
                    df = df[df["date"] <= end_date]
                df = df.sort_values("date")
            return df
        except Exception as e:
            logger.error(f"Failed to get futures kline for {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> StockInfo:
        return StockInfo(symbol=symbol, name=symbol, market="futures", industry="futures", sector="derivative")

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        return {"stock_name": symbol, "industry": "futures", "sector": "derivative", "contract_type": "futures"}

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.futures_display_main_sina()
            results = []
            if df is not None and not df.empty:
                for _, r in df.iterrows():
                    name = str(r.iloc[0]) if len(r) > 0 else ""
                    code = str(r.iloc[1]) if len(r) > 1 else name
                    if keyword.lower() in name.lower() or keyword.lower() in code.lower():
                        results.append({"code": code, "name": name, "market": "futures"})
                        if len(results) >= 20:
                            break
            return results
        except Exception as e:
            logger.error(f"Failed to search futures for {keyword}: {e}")
            return []
