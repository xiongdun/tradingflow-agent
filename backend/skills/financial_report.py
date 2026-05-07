# backend/skills/financial_report.py
# 财报三表解读技能 — 解读利润表/资产负债表/现金流量表关键指标

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="financial_report",
    description="解读财报三表（利润表/资产负债表/现金流量表），计算健康评分和风险警示",
    markets=["a_share", "us_stock"],
    category="fundamental",
)
def get_financial_report(symbol: str, market: str) -> dict[str, Any]:
    """获取并分析股票的财务报表数据"""
    provider = get_provider(market)

    result = {
        "symbol": symbol,
        "market": market,
        "income": {},
        "balance": {},
        "cashflow": {},
        "health_score": 50.0,
        "warnings": [],
    }

    if market == "a_share":
        return _analyze_a_share(result, symbol)
    elif market == "us_stock":
        return _analyze_us_stock(result, symbol, provider)
    return result


def _analyze_a_share(result: dict, symbol: str) -> dict:
    """分析 A 股财报数据"""
    import akshare as ak

    try:
        df_income = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
        if df_income is not None and not df_income.empty:
            latest = df_income.iloc[0]
            result["income"] = {
                "revenue": _to_float(latest.get("营业收入")),
                "net_profit": _to_float(latest.get("净利润")),
                "gross_margin": _to_float(latest.get("销售毛利率")),
                "net_margin": _to_float(latest.get("销售净利率")),
            }
    except Exception:
        pass

    try:
        df_balance = ak.stock_financial_report_sina(stock=symbol, symbol="资产负债表")
        if df_balance is not None and not df_balance.empty:
            latest = df_balance.iloc[0]
            total_assets = _to_float(latest.get("资产总计"))
            total_debt = _to_float(latest.get("负债合计"))
            result["balance"] = {
                "total_assets": total_assets,
                "total_debt": total_debt,
                "debt_ratio": round(total_debt / total_assets * 100, 2) if total_assets and total_debt else None,
                "current_ratio": _to_float(latest.get("流动比率")),
            }
    except Exception:
        pass

    try:
        df_cash = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
        if df_cash is not None and not df_cash.empty:
            latest = df_cash.iloc[0]
            result["cashflow"] = {
                "operating_cf": _to_float(latest.get("经营活动产生的现金流量净额")),
                "investing_cf": _to_float(latest.get("投资活动产生的现金流量净额")),
                "financing_cf": _to_float(latest.get("筹资活动产生的现金流量净额")),
            }
    except Exception:
        pass

    result["health_score"] = _calc_health_score(result)
    result["warnings"] = _check_warnings(result)
    return result


def _analyze_us_stock(result: dict, symbol: str, provider: Any) -> dict:
    """分析美股财报数据"""
    try:
        fin_data = provider.get_financial_data(symbol)
        if fin_data:
            result["income"] = {
                "revenue": fin_data.get("totalRevenue"),
                "net_profit": fin_data.get("netIncome"),
                "gross_margin": fin_data.get("grossMargins"),
            }
            result["balance"] = {
                "total_assets": fin_data.get("totalAssets"),
                "debt_ratio": fin_data.get("debtToEquity"),
            }
            result["cashflow"] = {
                "operating_cf": fin_data.get("operatingCashflow"),
                "free_cf": fin_data.get("freeCashflow"),
            }
    except Exception:
        pass

    result["health_score"] = _calc_health_score(result)
    result["warnings"] = _check_warnings(result)
    return result


def _calc_health_score(result: dict) -> float:
    """计算财务健康评分（0-100）"""
    score = 50.0
    income = result.get("income", {})
    balance = result.get("balance", {})
    cashflow = result.get("cashflow", {})

    if income.get("gross_margin") and income["gross_margin"] > 30:
        score += 10
    if income.get("net_margin") and income["net_margin"] > 10:
        score += 10

    debt_ratio = balance.get("debt_ratio")
    if debt_ratio is not None:
        if debt_ratio < 40:
            score += 10
        elif debt_ratio > 70:
            score -= 15

    if cashflow.get("operating_cf") and cashflow["operating_cf"] > 0:
        score += 10
    if cashflow.get("free_cf") and cashflow["free_cf"] > 0:
        score += 10

    return max(0, min(100, round(score, 1)))


def _check_warnings(result: dict) -> list[str]:
    """检查财务风险警示"""
    warnings = []
    balance = result.get("balance", {})
    cashflow = result.get("cashflow", {})
    income = result.get("income", {})

    debt_ratio = balance.get("debt_ratio")
    if debt_ratio and debt_ratio > 70:
        warnings.append(f"负债率偏高 ({debt_ratio}%)，财务杠杆风险大")

    if cashflow.get("operating_cf") and cashflow["operating_cf"] < 0:
        warnings.append("经营现金流为负，主营业务造血能力不足")

    if income.get("net_profit") and income["net_profit"] < 0:
        warnings.append("净利润为负，公司处于亏损状态")

    current_ratio = balance.get("current_ratio")
    if current_ratio and current_ratio < 1:
        warnings.append(f"流动比率偏低 ({current_ratio})，短期偿债压力大")

    return warnings


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return round(f, 2) if not (f != f) else None
    except (ValueError, TypeError):
        return None
