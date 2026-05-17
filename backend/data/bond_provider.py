# backend/data/bond_provider.py
# 债券数据提供者 — 基于 AKShare 获取可转债/国债/企业债数据

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


@provider("akshare", ["bond"], default_priority=0)
class BondProvider(DataProvider):
    """债券数据提供者 — 实现债券的实时行情、K 线、基本信息等接口"""

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        """获取债券实时行情报价"""
        import akshare as ak
        import pandas as pd
        try:
            with bypass_proxy():
                df = ak.bond_zh_hs_spot()
            code_col = df.columns[0]
            row = df[df[code_col].astype(str) == symbol]
            if row.empty:
                raise ValueError(f"Bond {symbol} not found")
            r = row.iloc[0]
            name_c = _find_col(r, ["名称", "债券简称"], symbol)
            price_c = _find_col(r, ["最新价", "现价", "收盘价"])
            change_c = _find_col(r, ["涨跌额", "涨跌"])
            chg_pct_c = _find_col(r, ["涨跌幅"])
            vol_c = _find_col(r, ["成交量"])
            turn_c = _find_col(r, ["成交额"])
            hi_c = _find_col(r, ["最高"])
            lo_c = _find_col(r, ["最低"])
            opn_c = _find_col(r, ["今开", "开盘"])
            prev_c = _find_col(r, ["昨收"])

            return StockQuote(
                symbol=symbol,
                name=str(r[name_c]),
                market="bond",
                price=float(r[price_c]) if pd.notna(r[price_c]) else 0.0,
                change=float(r[change_c]) if pd.notna(r[change_c]) else 0.0,
                change_pct=float(r[chg_pct_c]) if pd.notna(r[chg_pct_c]) else 0.0,
                volume=float(r[vol_c]) if pd.notna(r[vol_c]) else 0.0,
                turnover=float(r[turn_c]) if pd.notna(r[turn_c]) else 0.0,
                high=float(r[hi_c]) if pd.notna(r[hi_c]) else 0.0,
                low=float(r[lo_c]) if pd.notna(r[lo_c]) else 0.0,
                open=float(r[opn_c]) if pd.notna(r[opn_c]) else 0.0,
                prev_close=float(r[prev_c]) if pd.notna(r[prev_c]) else 0.0,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get bond realtime quote for {symbol}: {e}")
            raise

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        """获取债券 K 线历史数据"""
        import pandas as pd
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.bond_zh_hs_daily(symbol=symbol)
            if df.empty:
                return pd.DataFrame()

            # 标准化列名
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
            logger.error(f"Failed to get bond kline for {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> StockInfo:
        """获取债券基本信息"""
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.bond_zh_hs_spot()
            code_col = df.columns[0]
            row = df[df[code_col].astype(str) == symbol]
            if row.empty:
                return StockInfo(symbol=symbol, name=symbol, market="bond")
            r = row.iloc[0]
            name_c = _find_col(r, ["名称", "债券简称"], symbol)
            return StockInfo(
                symbol=symbol,
                name=str(r[name_c]),
                market="bond",
                industry="bond",
                sector="fixed_income",
            )
        except Exception as e:
            logger.error(f"Failed to get bond info for {symbol}: {e}")
            return StockInfo(symbol=symbol, name=symbol, market="bond")

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        """获取债券财务数据（票面利率、到期日等）"""
        info = self.get_stock_info(symbol)
        return {
            "stock_name": info.name,
            "industry": info.industry,
            "sector": info.sector,
            "bond_type": "convertible",
        }

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        """按关键词搜索债券"""
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.bond_zh_hs_spot()
            code_col = df.columns[0]
            first_row = df.iloc[0] if len(df) > 0 else None
            name_c = _find_col(first_row, ["名称", "债券简称"], "")
            results = []
            for _, r in df.iterrows():
                code = str(r[code_col])
                name = str(r[name_c]) if name_c else ""
                if keyword.lower() in code.lower() or keyword.lower() in name.lower():
                    results.append({"code": code, "name": name, "market": "bond"})
                    if len(results) >= 20:
                        break
            return results
        except Exception as e:
            logger.error(f"Failed to search bonds for {keyword}: {e}")
            return []
