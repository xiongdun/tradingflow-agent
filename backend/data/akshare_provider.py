# backend/data/akshare_provider.py
# AKShare 数据提供者 — 基于 AKShare 库获取 A 股和港股数据

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from backend.data.provider import DataProvider, StockInfo, StockQuote, bypass_proxy, provider


def _is_hk_symbol(symbol: str) -> bool:
    """判断是否为港股代码（5 位数字，如 00700）"""
    return len(symbol) == 5 and symbol.isdigit()


@provider("akshare", ["a_share", "h_stock"], default_priority=0)
class AKShareProvider(DataProvider):
    """AKShare 数据提供者 — 实现 A 股/港股的实时行情、K 线、财务数据等接口"""

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        """获取实时行情报价（A 股或港股自动识别）"""
        if _is_hk_symbol(symbol):
            return self._get_hk_realtime_quote(symbol)
        return self._get_a_realtime_quote(symbol)

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        """获取 K 线历史数据（A 股或港股自动识别）"""
        if _is_hk_symbol(symbol):
            return self._get_hk_kline(symbol, period, start_date, end_date)
        return self._get_a_kline(symbol, period, start_date, end_date)

    def get_stock_info(self, symbol: str) -> StockInfo:
        """获取股票基本信息（A 股或港股自动识别）"""
        if _is_hk_symbol(symbol):
            return self._get_hk_stock_info(symbol)
        return self._get_a_stock_info(symbol)

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        """获取财务数据（A 股或港股自动识别）"""
        if _is_hk_symbol(symbol):
            return self._get_hk_financial_data(symbol)
        return self._get_a_financial_data(symbol)

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        """按关键词搜索股票（A 股 + 港股）"""
        results = self._search_a_share(keyword)
        results.extend(self._search_hk(keyword))
        return results

    # ──────────────────────────── A 股实现 ────────────────────────────

    def _get_a_realtime_quote(self, symbol: str) -> StockQuote:
        """获取 A 股实时行情报价"""
        import akshare as ak
        import pandas as pd
        try:
            with bypass_proxy():
                df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == symbol]
            if row.empty:
                raise ValueError(f"Stock {symbol} not found")
            r = row.iloc[0]
            return StockQuote(
                symbol=symbol,
                name=str(r["名称"]),
                market="a_share",
                price=float(r["最新价"]) if pd.notna(r["最新价"]) else 0.0,
                change=float(r["涨跌额"]) if pd.notna(r["涨跌额"]) else 0.0,
                change_pct=float(r["涨跌幅"]) if pd.notna(r["涨跌幅"]) else 0.0,
                volume=float(r["成交量"]) if pd.notna(r["成交量"]) else 0.0,
                turnover=float(r["成交额"]) if pd.notna(r["成交额"]) else 0.0,
                high=float(r["最高"]) if pd.notna(r["最高"]) else 0.0,
                low=float(r["最低"]) if pd.notna(r["最低"]) else 0.0,
                open=float(r["今开"]) if pd.notna(r["今开"]) else 0.0,
                prev_close=float(r["昨收"]) if pd.notna(r["昨收"]) else 0.0,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get realtime quote for {symbol}: {e}")
            raise

    def _get_a_kline(self, symbol: str, period: str = "daily",
                     start_date: str | None = None, end_date: str | None = None):
        """获取 A 股 K 线历史数据（OHLCV），支持前复权"""
        import akshare as ak
        try:
            period_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
            ak_period = period_map.get(period, "daily")
            with bypass_proxy():
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period=ak_period,
                    start_date=start_date.replace("-", "") if start_date else "20240101",
                    end_date=end_date.replace("-", "") if end_date else datetime.now().strftime("%Y%m%d"),
                    adjust="qfq",
                )
            df = df.rename(columns={
                "日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume",
                "成交额": "turnover", "振幅": "amplitude",
                "涨跌幅": "change_pct", "涨跌额": "change",
                "换手率": "turnover_rate",
            })
            return df
        except Exception as e:
            logger.error(f"Failed to get kline for {symbol}: {e}")
            raise

    def _get_a_stock_info(self, symbol: str) -> StockInfo:
        """获取 A 股基本信息（名称/市盈率/市净率/总市值）"""
        import akshare as ak
        import pandas as pd
        try:
            with bypass_proxy():
                df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == symbol]
            if row.empty:
                raise ValueError(f"Stock {symbol} not found")
            r = row.iloc[0]
            return StockInfo(
                symbol=symbol,
                name=str(r["名称"]),
                market="a_share",
                pe_ratio=float(r["市盈率-动态"]) if pd.notna(r.get("市盈率-动态")) else 0.0,
                pb_ratio=float(r["市净率"]) if pd.notna(r.get("市净率")) else 0.0,
                market_cap=float(r["总市值"]) if pd.notna(r.get("总市值")) else 0.0,
            )
        except Exception as e:
            logger.error(f"Failed to get stock info for {symbol}: {e}")
            raise

    def _get_a_financial_data(self, symbol: str) -> dict[str, Any]:
        """获取 A 股财务指标（PE/PB/市值/量比/换手率/振幅等）"""
        import akshare as ak
        import pandas as pd
        try:
            with bypass_proxy():
                df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == symbol]
            if row.empty:
                return {}
            r = row.iloc[0]
            return {
                "pe_ratio": float(r["市盈率-动态"]) if pd.notna(r.get("市盈率-动态")) else None,
                "pb_ratio": float(r["市净率"]) if pd.notna(r.get("市净率")) else None,
                "total_market_cap": float(r["总市值"]) if pd.notna(r.get("总市值")) else None,
                "circulating_market_cap": float(r["流通市值"]) if pd.notna(r.get("流通市值")) else None,
                "volume_ratio": float(r["量比"]) if pd.notna(r.get("量比")) else None,
                "turnover_rate": float(r["换手率"]) if pd.notna(r.get("换手率")) else None,
                "amplitude": float(r["振幅"]) if pd.notna(r.get("振幅")) else None,
                "high_52w": float(r["年初至今涨跌幅"]) if pd.notna(r.get("年初至今涨跌幅")) else None,
            }
        except Exception as e:
            logger.error(f"Failed to get financial data for {symbol}: {e}")
            return {}

    def _search_a_share(self, keyword: str) -> list[dict[str, str]]:
        """按名称或代码关键词搜索 A 股股票"""
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.stock_zh_a_spot_em()
            mask = df["名称"].str.contains(keyword, na=False) | df["代码"].str.contains(keyword, na=False)
            results = df[mask].head(10)
            return [
                {"symbol": str(row["代码"]), "name": str(row["名称"]), "market": "a_share"}
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"Failed to search stocks: {e}")
            return []

    # ──────────────────────────── 港股实现 ────────────────────────────

    def _get_hk_realtime_quote(self, symbol: str) -> StockQuote:
        """获取港股实时行情报价"""
        import akshare as ak
        import pandas as pd
        try:
            with bypass_proxy():
                df = ak.stock_hk_spot_em()
            # 港股代码可能有前导零，尝试多种匹配
            code_col = "代码" if "代码" in df.columns else "股票代码"
            row = df[df[code_col] == symbol]
            if row.empty:
                row = df[df[code_col] == symbol.lstrip("0")]
            if row.empty:
                row = df[df[code_col].astype(str).str.endswith(symbol)]
            if row.empty:
                raise ValueError(f"HK stock {symbol} not found")
            r = row.iloc[0]

            def _float(*col_names: str) -> float:
                for c in col_names:
                    val = r.get(c)
                    if val is not None and not (isinstance(val, float) and pd.isna(val)):
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            pass
                return 0.0

            return StockQuote(
                symbol=symbol,
                name=str(r.get("名称", r.get("股票名称", symbol))),
                market="h_stock",
                price=_float("最新价", "现价"),
                change=_float("涨跌额"),
                change_pct=_float("涨跌幅"),
                volume=_float("成交量"),
                turnover=_float("成交额"),
                high=_float("最高"),
                low=_float("最低"),
                open=_float("今开", "开盘"),
                prev_close=_float("昨收"),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get HK realtime quote for {symbol}: {e}")
            raise

    def _get_hk_kline(self, symbol: str, period: str = "daily",
                      start_date: str | None = None, end_date: str | None = None):
        """获取港股 K 线历史数据"""
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.stock_hk_hist(
                    symbol=symbol,
                    period=period,
                    start_date=start_date.replace("-", "") if start_date else "20240101",
                    end_date=end_date.replace("-", "") if end_date else datetime.now().strftime("%Y%m%d"),
                    adjust="qfq",
                )
            # 统一列名（兼容 AKShare 不同版本的列名）
            col_map = {}
            for target, candidates in {
                "date": ["日期", "Date"],
                "open": ["开盘", "Open"],
                "close": ["收盘", "Close"],
                "high": ["最高", "High"],
                "low": ["最低", "Low"],
                "volume": ["成交量", "Volume"],
                "turnover": ["成交额", "Turnover"],
                "amplitude": ["振幅", "Amplitude"],
                "change_pct": ["涨跌幅", "Change%"],
                "change": ["涨跌额", "Change"],
                "turnover_rate": ["换手率", "Turnover Rate"],
            }.items():
                for c in candidates:
                    if c in df.columns:
                        col_map[c] = target
                        break
            df = df.rename(columns=col_map)
            return df
        except Exception as e:
            logger.error(f"Failed to get HK kline for {symbol}: {e}")
            raise

    def _get_hk_stock_info(self, symbol: str) -> StockInfo:
        """获取港股基本信息"""
        import akshare as ak
        import pandas as pd
        try:
            with bypass_proxy():
                df = ak.stock_hk_spot_em()
            code_col = "代码" if "代码" in df.columns else "股票代码"
            row = df[df[code_col] == symbol]
            if row.empty:
                row = df[df[code_col] == symbol.lstrip("0")]
            if row.empty:
                raise ValueError(f"HK stock {symbol} not found")
            r = row.iloc[0]

            def _float(*cols: str) -> float:
                for c in cols:
                    val = r.get(c)
                    if val is not None and not (isinstance(val, float) and pd.isna(val)):
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            pass
                return 0.0

            return StockInfo(
                symbol=symbol,
                name=str(r.get("名称", r.get("股票名称", symbol))),
                market="h_stock",
                pe_ratio=_float("市盈率", "市盈率(动态)"),
                pb_ratio=_float("市净率"),
                market_cap=_float("总市值"),
            )
        except Exception as e:
            logger.error(f"Failed to get HK stock info for {symbol}: {e}")
            raise

    def _get_hk_financial_data(self, symbol: str) -> dict[str, Any]:
        """获取港股财务指标"""
        import akshare as ak
        import pandas as pd
        try:
            with bypass_proxy():
                df = ak.stock_hk_spot_em()
            code_col = "代码" if "代码" in df.columns else "股票代码"
            row = df[df[code_col] == symbol]
            if row.empty:
                row = df[df[code_col] == symbol.lstrip("0")]
            if row.empty:
                return {}
            r = row.iloc[0]

            def _opt_float(*cols: str) -> float | None:
                for c in cols:
                    val = r.get(c)
                    if val is not None and not (isinstance(val, float) and pd.isna(val)):
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            pass
                return None

            return {
                "pe_ratio": _opt_float("市盈率", "市盈率(动态)"),
                "pb_ratio": _opt_float("市净率"),
                "total_market_cap": _opt_float("总市值"),
                "circulating_market_cap": _opt_float("流通市值"),
                "turnover_rate": _opt_float("换手率"),
            }
        except Exception as e:
            logger.error(f"Failed to get HK financial data for {symbol}: {e}")
            return {}

    def _search_hk(self, keyword: str) -> list[dict[str, str]]:
        """按名称或代码关键词搜索港股"""
        import akshare as ak
        try:
            with bypass_proxy():
                df = ak.stock_hk_spot_em()
            code_col = "代码" if "代码" in df.columns else "股票代码"
            name_col = "名称" if "名称" in df.columns else "股票名称"
            mask = df[name_col].str.contains(keyword, na=False) | df[code_col].str.contains(keyword, na=False)
            results = df[mask].head(10)
            return [
                {"symbol": str(row[code_col]), "name": str(row[name_col]), "market": "h_stock"}
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"Failed to search HK stocks: {e}")
            return []
