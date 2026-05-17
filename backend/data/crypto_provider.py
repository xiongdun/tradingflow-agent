# backend/data/crypto_provider.py
# 加密货币数据提供者 — 基于 yfinance 获取 BTC/ETH 等加密货币数据

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from backend.data.provider import DataProvider, StockInfo, StockQuote, provider

_CRYPTO_NAMES: dict[str, str] = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "BNB": "Binance Coin",
    "SOL": "Solana", "XRP": "Ripple", "ADA": "Cardano",
    "DOGE": "Dogecoin", "AVAX": "Avalanche", "DOT": "Polkadot",
    "MATIC": "Polygon", "LINK": "Chainlink", "UNI": "Uniswap",
    "SHIB": "Shiba Inu", "LTC": "Litecoin", "ATOM": "Cosmos",
    "FIL": "Filecoin", "APT": "Aptos", "ARB": "Arbitrum",
    "OP": "Optimism", "SUI": "Sui",
}


def _to_yf_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    if s.endswith("-USD") or s.endswith("-USDT"):
        return s
    return f"{s}-USD"


@provider("yfinance", ["crypto"], default_priority=0)
class CryptoProvider(DataProvider):
    """加密货币数据提供者 — 基于 yfinance 获取加密货币行情数据"""

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        import yfinance as yf
        try:
            yf_sym = _to_yf_symbol(symbol)
            ticker = yf.Ticker(yf_sym)
            info = ticker.info
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
            return StockQuote(
                symbol=symbol,
                name=info.get("shortName", _CRYPTO_NAMES.get(symbol.upper(), symbol)),
                market="crypto",
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
            logger.error(f"Failed to get crypto quote for {symbol}: {e}")
            raise

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        import pandas as pd
        import yfinance as yf
        try:
            yf_sym = _to_yf_symbol(symbol)
            ticker = yf.Ticker(yf_sym)
            period_map = {"daily": "1d", "weekly": "1wk", "monthly": "1mo"}
            df = ticker.history(period="1y", interval=period_map.get(period, "1d"))
            if df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            if "date" not in df.columns and "datetime" in df.columns:
                df = df.rename(columns={"datetime": "date"})
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                if start_date:
                    df = df[df["date"] >= start_date]
                if end_date:
                    df = df[df["date"] <= end_date]
            return df
        except Exception as e:
            logger.error(f"Failed to get crypto kline for {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> StockInfo:
        import yfinance as yf
        try:
            yf_sym = _to_yf_symbol(symbol)
            info = yf.Ticker(yf_sym).info
            return StockInfo(
                symbol=symbol,
                name=info.get("shortName", _CRYPTO_NAMES.get(symbol.upper(), symbol)),
                market="crypto", industry="cryptocurrency", sector="digital_asset",
                market_cap=float(info.get("marketCap", 0)),
            )
        except Exception:
            return StockInfo(symbol=symbol, name=_CRYPTO_NAMES.get(symbol.upper(), symbol), market="crypto")

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        import yfinance as yf
        try:
            info = yf.Ticker(_to_yf_symbol(symbol)).info
            return {
                "stock_name": info.get("shortName", symbol),
                "market_cap": info.get("marketCap", 0),
                "total_volume": info.get("totalVolume", 0),
                "circulating_supply": info.get("circulatingSupply", 0),
                "max_supply": info.get("maxSupply", 0),
                "ath": info.get("fiftyTwoWeekHigh", 0),
                "atl": info.get("fiftyTwoWeekLow", 0),
            }
        except Exception:
            return {"stock_name": symbol}

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        results = []
        kw = keyword.upper()
        for sym, name in _CRYPTO_NAMES.items():
            if kw in sym or keyword.lower() in name.lower():
                results.append({"code": sym, "name": name, "market": "crypto"})
            if len(results) >= 20:
                break
        return results
