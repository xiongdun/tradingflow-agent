# 功能增强设计文档：新 Agent + 新技能 + 工作流引擎升级

**日期：** 2026-05-01
**方案：** A+C 组合（深度扩展分析能力 + 工作流引擎升级）

## 1. 概述

### 目标
在现有 6 Agent + 8 技能 + 2 工作流模板的基础上，大幅扩展分析能力和工作流灵活性。

### 范围
- 新增 3 个 Agent 角色
- 新增 6 个技能插件
- 升级工作流引擎，支持条件分支、多轮迭代、自适应选择
- 新增 3 个预置工作流模板

## 2. 新增 Agent 角色

### 2.1 板块轮动分析师 (`sector_rotation`)

- **文件：** `backend/agents/sector_rotation.py`
- **视角：** 自上而下，从板块到个股
- **默认技能：** `sector_flow`, `realtime_quote`, `kline_data`
- **系统提示词核心：**
  - 追踪板块资金轮动方向
  - 识别市场主线题材和支线题材
  - 判断板块所处阶段（启动/加速/分化/退潮）
  - 从板块龙头反推个股机会

### 2.2 量化分析师 (`quant`)

- **文件：** `backend/agents/quant.py`
- **视角：** 数据驱动，统计和因子分析
- **默认技能：** `kline_data`, `technical_indicators`, `financial_data`
- **系统提示词核心：**
  - 计算技术指标组合信号（MA 金叉/死叉、MACD 背离、RSI 超买超卖）
  - 量价关系统计分析
  - 因子打分（估值因子、动量因子、质量因子）
  - 回测胜率和盈亏比估算

### 2.3 风控分析师 (`risk`)

- **文件：** `backend/agents/risk.py`
- **视角：** 风险优先，保护本金
- **默认技能：** `kline_data`, `financial_data`, `realtime_quote`, `sentiment_scan`
- **系统提示词核心：**
  - 波动率和 VaR 估算
  - 最大回撤评估
  - 流动性风险（成交量萎缩、跌停风险）
  - 仓位建议（轻仓/半仓/重仓/空仓）
  - 止损位建议

### 注册更新

在 `backend/agents/registry.py` 的 `_AGENT_MAP` 中添加：

```python
from backend.agents.sector_rotation import SectorRotationAgent
from backend.agents.quant import QuantAgent
from backend.agents.risk import RiskAgent

_AGENT_MAP = {
    ...,
    "sector_rotation": SectorRotationAgent,
    "quant": QuantAgent,
    "risk": RiskAgent,
}
```

## 3. 新增技能插件

### 3.1 technical_indicators（技术指标计算）

- **文件：** `backend/skills/technical_indicators.py`
- **类别：** technical
- **支持市场：** a_share, h_stock, us_stock
- **实现逻辑：** 基于 kline 数据本地计算，无需额外 API 调用
- **返回结构：**
```python
{
    "ma": {"ma5": float, "ma10": float, "ma20": float, "ma60": float, "signal": "bullish/bearish"},
    "macd": {"dif": float, "dea": float, "histogram": float, "signal": "golden_cross/dead_cross/neutral"},
    "rsi": {"rsi6": float, "rsi14": float, "signal": "overbought/oversold/neutral"},
    "boll": {"upper": float, "middle": float, "lower": float, "position": "above/within/below"},
    "kdj": {"k": float, "d": float, "j": float, "signal": "golden_cross/dead_cross/neutral"},
    "overall_signal": "bullish/bearish/neutral",
    "signal_count": {"bullish": int, "bearish": int, "neutral": int}
}
```
- **依赖：** pandas, numpy（已安装）

### 3.2 limit_up_analysis（涨停板分析）

- **文件：** `backend/skills/limit_up_analysis.py`
- **类别：** sentiment
- **支持市场：** a_share
- **数据源：** `ak.stock_zt_pool_em()`（涨停池）、`ak.stock_zt_pool_zbgc_em()`（炸板股）
- **返回结构：**
```python
{
    "is_limit_up": bool,
    "consecutive_days": int,
    "limit_up_reason": str,
    "sector": str,
    "break_rate": float,
    "similar_stocks": list
}
```

### 3.3 block_trade（大宗交易）

- **文件：** `backend/skills/block_trade.py`
- **类别：** data
- **支持市场：** a_share
- **数据源：** `ak.stock_dzjy_sctj()`（大宗交易统计）
- **返回结构：**
```python
{
    "recent_trades": [{"date": str, "price": float, "volume": float, "premium_discount": float}],
    "summary": str,
    "net_direction": "buy/sell/neutral"
}
```

### 3.4 shareholder_analysis（股东分析）

- **文件：** `backend/skills/shareholder_analysis.py`
- **类别：** fundamental
- **支持市场：** a_share
- **数据源：** `ak.stock_gdfx_free_holding_analyse_em()`（前十大流通股东）
- **返回结构：**
```python
{
    "top10_holders": [{"name": str, "holding_pct": float, "change": str}],
    "institution_count": int,
    "institution_holding_pct": float,
    "change_trend": "increasing/decreasing/stable"
}
```

### 3.5 fund_flow（主力资金流向）

- **文件：** `backend/skills/fund_flow.py`
- **类别：** sentiment
- **支持市场：** a_share
- **数据源：** `ak.stock_individual_fund_flow()`（个股资金流）
- **返回结构：**
```python
{
    "main_net_inflow": float,
    "super_large_net": float,
    "large_net": float,
    "medium_net": float,
    "small_net": float,
    "trend": "inflow/outflow/neutral",
    "days_inflow": int
}
```

### 3.6 financial_report（财报三表解读）

- **文件：** `backend/skills/financial_report.py`
- **类别：** fundamental
- **支持市场：** a_share, us_stock
- **数据源：** AKShare 财报接口 / yfinance
- **返回结构：**
```python
{
    "income": {"revenue": float, "net_profit": float, "gross_margin": float, "yoy_growth": float},
    "balance": {"total_assets": float, "total_debt": float, "debt_ratio": float, "current_ratio": float},
    "cashflow": {"operating_cf": float, "investing_cf": float, "financing_cf": float, "free_cf": float},
    "health_score": float,
    "warnings": list[str]
}
```

## 4. 工作流引擎升级

### 4.1 当前状态

- `builder.py` 只支持并行扇出-扇入模式
- 辩论模式是硬编码特例（`workflows/debate.py`）
- 不支持条件分支、多轮迭代、动态 Agent 选择

### 4.2 升级方案

#### 4.2.1 条件分支模式

在 `builder.py` 中新增 `build_conditional_workflow()` 函数：

```python
def build_conditional_workflow(stages: list[dict]) -> Any:
    """
    stages 格式：
    [
        {"agents": ["risk"], "condition": "always"},
        {"agents": ["fundamental", "technical"], "condition": "risk.stance != 'bearish'"},
    ]
    """
```

**实现方式：** 使用 LangGraph 的 `add_conditional_edges()`，根据 state 中的 opinions 动态路由。

#### 4.2.2 多轮迭代模式

新增 `build_multi_round_workflow()` 函数：

```python
def build_multi_round_workflow(agents: list[str], rounds: int = 2) -> Any:
    """
    执行流程：
    START → [第一轮并行] → cross_review → [修正并行] → ... → summarizer → END
    """
```

**实现方式：**
1. 每轮分析师执行后，添加 `cross_review` 节点
2. `cross_review` 将所有意见作为上下文传回分析师
3. 分析师修正意见后进入下一轮
4. 使用 LangGraph 的循环边实现多轮

#### 4.2.3 自适应 Agent 选择

新增 `build_adaptive_workflow()` 函数：

```python
def build_adaptive_workflow() -> Any:
    """
    执行流程：
    START → selector → [选中的分析师] → summarizer → END
    """
```

**selector 节点逻辑：**
1. 获取股票基本信息（市值、行业、换手率）
2. 根据特征选择 Agent 组合：
   - 大盘蓝筹（市值 > 1000 亿）→ fundamental, macro, quant
   - 小盘题材（市值 < 100 亿，换手率 > 5%）→ hot_money, sentiment, news
   - 科技成长 → technical, fundamental, news, quant
   - 默认 → fundamental, technical, sentiment

### 4.3 新工作流模板

#### full_spectrum（全频谱分析）

```json
{
  "name": "full_spectrum",
  "description": "全频谱分析：所有分析师参与，适合深度研究",
  "mode": "parallel",
  "agents": [
    {"role": "fundamental"},
    {"role": "technical"},
    {"role": "sentiment"},
    {"role": "news"},
    {"role": "macro"},
    {"role": "hot_money"},
    {"role": "sector_rotation"},
    {"role": "quant"},
    {"role": "risk"}
  ]
}
```

#### risk_first（风控优先）

```json
{
  "name": "risk_first",
  "description": "风控优先：先评估风险，再决定是否深入分析",
  "mode": "conditional",
  "stages": [
    {"agents": ["risk"], "condition": "always"},
    {"agents": ["fundamental", "technical", "quant"], "condition": "check_risk"},
    {"agents": ["sentiment", "news"], "condition": "always"}
  ],
  "summarizer_prompt": "请特别关注风控分析师的风险提示，如果风控分析师给出空仓建议，请在报告中明确标注高风险。"
}
```

#### debate_v2（增强辩论）

```json
{
  "name": "debate_v2",
  "description": "增强辩论：多轮交叉审阅，适合争议性标的",
  "mode": "multi_round",
  "rounds": 2,
  "agents": ["fundamental", "technical", "sentiment", "quant"],
  "summarizer_prompt": "请重点分析多轮辩论中观点的变化和收敛情况。"
}
```

## 5. 实现顺序

### Phase 1：新增技能（1-2 天）
1. `technical_indicators` — 本地计算，无外部依赖
2. `fund_flow` — AKShare 已有接口
3. `limit_up_analysis` — AKShare 已有接口
4. `block_trade` — AKShare 已有接口
5. `shareholder_analysis` — AKShare 已有接口
6. `financial_report` — AKShare + yfinance

### Phase 2：新增 Agent（1 天）
1. `quant` — 使用 technical_indicators 技能
2. `sector_rotation` — 使用 sector_flow 技能
3. `risk` — 使用 kline_data + financial_data 技能

### Phase 3：工作流引擎升级（2-3 天）
1. 条件分支模式 `build_conditional_workflow()`
2. 多轮迭代模式 `build_multi_round_workflow()`
3. 自适应选择模式 `build_adaptive_workflow()`
4. 新工作流模板 JSON

### Phase 4：前端适配（1 天）
1. 工作流模板选择器支持新模式
2. 分析结果展示新增 Agent 意见
3. 条件分支可视化（可选）

## 6. 文件变更清单

### 新增文件
- `backend/agents/sector_rotation.py`
- `backend/agents/quant.py`
- `backend/agents/risk.py`
- `backend/skills/technical_indicators.py`
- `backend/skills/limit_up_analysis.py`
- `backend/skills/block_trade.py`
- `backend/skills/shareholder_analysis.py`
- `backend/skills/fund_flow.py`
- `backend/skills/financial_report.py`
- `backend/graph/templates/full_spectrum.json`
- `backend/graph/templates/risk_first.json`
- `backend/graph/templates/debate_v2.json`

### 修改文件
- `backend/agents/registry.py` — 注册新 Agent
- `backend/graph/builder.py` — 新增条件分支、多轮迭代、自适应选择构建函数
- `backend/graph/state.py` — 扩展状态字段（如 `round`, `selected_agents`）
- `backend/main.py` — 导入新技能模块
- `backend/cli.py` — 导入新技能模块

## 7. 验证标准

- [ ] 所有新技能可通过 `tradingflow skills` 命令列出
- [ ] 所有新 Agent 可通过 `tradingflow agents-list` 命令列出
- [ ] 新工作流模板可通过 `GET /api/workflows` 返回
- [ ] `tradingflow analyze 600519 --workflow full_spectrum` 能正常执行
- [ ] `tradingflow analyze 600519 --workflow risk_first` 能正常执行条件分支
- [ ] `tradingflow analyze 600519 --workflow debate_v2` 能正常执行多轮辩论
- [ ] 前端工作流选择器能显示新模板
