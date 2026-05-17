# backend/skills/news_fetch.py
# 新闻获取技能 — 获取股票相关新闻资讯

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="news_fetch",
    description="获取股票相关新闻资讯，用于新闻面分析和事件驱动分析",
    markets=["a_share", "h_stock", "us_stock", "bond", "futures", "crypto"],
    category="news",
    label="新闻资讯",
)
def fetch_news(symbol: str, market: str, limit: int = 10) -> dict[str, Any]:
    """获取股票最近新闻。A股使用 AKShare，港股/美股使用 yfinance"""
    try:
        if market == "a_share":
            return _fetch_a_share_news(symbol, limit)
        else:
            return _fetch_yfinance_news(symbol, market, limit)
    except Exception as e:
        return {"symbol": symbol, "market": market, "news": [], "error": str(e)}


def _fetch_a_share_news(symbol: str, limit: int) -> dict[str, Any]:
    """通过 AKShare 获取 A 股新闻"""
    import akshare as ak
    try:
        df = ak.stock_news_em(symbol=symbol)
        if df is None or df.empty:
            return {"symbol": symbol, "market": "a_share", "news": []}

        news = []
        for _, row in df.head(limit).iterrows():
            news.append({
                "title": str(row.get("新闻标题", "")),
                "content": str(row.get("新闻内容", ""))[:500],
                "source": str(row.get("文章来源", "")),
                "time": str(row.get("发布时间", "")),
                "url": str(row.get("新闻链接", "")),
            })
        return {"symbol": symbol, "market": "a_share", "news": news}
    except Exception as e:
        return {"symbol": symbol, "market": "a_share", "news": [], "error": str(e)}


def _fetch_yfinance_news(symbol: str, market: str, limit: int) -> dict[str, Any]:
    """通过 yfinance 获取港股/美股新闻（兼容多种 yfinance 版本的数据结构）"""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news or []
        news = []
        for item in raw_news[:limit]:
            # yfinance 不同版本返回结构不同，兼容处理
            content = item.get("content", item)
            title = (
                content.get("title")
                or item.get("title")
                or item.get("headline", "")
            )
            summary = (
                content.get("summary")
                or content.get("description")
                or item.get("summary", "")
            )
            source: str = ""
            provider = content.get("provider", {})
            if isinstance(provider, dict):
                source = str(provider.get("displayName", provider.get("name", "")) or "")
            elif isinstance(provider, str):
                source = provider
            pub_date = (
                content.get("pubDate")
                or content.get("pubdate")
                or item.get("providerPublishTime", "")
            )
            url = ""
            canon = content.get("canonicalUrl", {})
            if isinstance(canon, dict):
                url = canon.get("url", "")
            elif isinstance(canon, str):
                url = canon
            if not url:
                url = item.get("link", "")

            if title:  # 至少要有标题才收录
                news.append({
                    "title": title,
                    "content": (summary or "")[:500],
                    "source": source,
                    "time": str(pub_date),
                    "url": url,
                })
        return {"symbol": symbol, "market": market, "news": news}
    except Exception as e:
        return {"symbol": symbol, "market": market, "news": [], "error": str(e)}
