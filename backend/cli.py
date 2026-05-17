# backend/cli.py
# CLI 命令行入口 — 通过 Typer 提供命令行股票分析工具

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from backend.graph import TEMPLATES_DIR
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

app = typer.Typer(
    name="tradingflow",
    help="🤖 TradingFlow Agent — AI 多智能体股票分析系统",
    no_args_is_help=True,
)
console = Console()

_SAMPLE_REPORT = """
# 📊 贵州茅台 (600519) 分析报告

## 🏷️ 综合研判
**投资评级：增持** | 风险等级：低

贵州茅台作为A股价值投资标杆，具备极强的品牌护城河和定价权。
当前估值处于历史中位，现金流充裕，股息率稳中有升。

## 📈 基本面分析
- 市盈率(TTM)：28.5x，处于近5年 40% 分位
- ROE：32.1%，远超行业平均
- 毛利率：91.5%，护城河极深
- 资产负债率：19.2%，财务极度健康

## 📉 技术面分析
- 均线排列：多头排列，MA5>MA20>MA60
- MACD：金叉形成，红柱放大
- RSI(14)：58.3，中性偏强区间
- 支撑位：1,600 | 压力位：1,850

## 🎯 策略建议
- 长期投资者：当前位置可分批建仓，目标仓位15-20%
- 波段交易者：关注1600支撑，跌破减仓；突破1850可加仓
- 风险提示：消费复苏不及预期、白酒行业政策风险

> ⚠️ 本报告由 AI 生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。
"""


@app.command()
def demo():
    """🎓 零配置演示 — 无需 API Key，看看分析报告长什么样"""
    console.print(Panel.fit(
        "[bold cyan]🎓 欢迎来到 TradingFlow Agent 演示模式！[/bold cyan]\n\n"
        "这是 [green]零配置[/green] 的演示分析报告，完全不需要 API Key。\n"
        "真实分析需要配置 LLM 大模型，只需 3 步：\n\n"
        "  [yellow]1.[/yellow] 注册 DeepSeek: https://platform.deepseek.com\n"
        "  [yellow]2.[/yellow] 创建 API Key，复制密钥\n"
        "  [yellow]3.[/yellow] 在 .env 中填写 LLM_API_KEY=你的密钥\n\n"
        "配置完成后运行: [bold]tradingflow analyze 600519[/bold] 开始真实分析",
        title="🚀 使用指南",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()
    console.print(Markdown(_SAMPLE_REPORT))
    console.print()
    console.print("[dim]📌 上面是一份静态示例报告，真实分析将由 AI 大模型实时生成，内容更详尽、更个性化[/dim]")


@app.command()
def analyze(
    symbol: str = typer.Argument(help="股票代码 (如: 600519, AAPL)"),
    market: str = typer.Option("a_share", "--market", "-m", help="市场: a_share, h_stock, us_stock, bond, futures, crypto"),
    workflow: str = typer.Option("deep_analysis", "--workflow", "-w", help="工作流模板: quick_scan, deep_analysis, debate"),
    agents: str = typer.Option("", "--agents", "-a", help="指定 Agent (逗号分隔): fundamental,technical,sentiment,news,macro"),
    output: str = typer.Option("", "--output", "-o", help="输出文件路径 (默认打印到终端)"),
):
    """运行股票分析，支持自定义工作流和 Agent 组合"""
    from backend.core.discovery import auto_discover
    auto_discover()

    console.print(f"\n🚀 [bold]开始分析 {symbol} ({market})[/bold]\n")

    # 加载工作流定义：优先使用 --agents 参数，否则从模板文件加载
    if agents:
        agent_list = [a.strip() for a in agents.split(",")]
        workflow_def = {"name": "custom", "agents": [{"role": r} for r in agent_list]}
    else:
        template_path = TEMPLATES_DIR / f"{workflow}.json"
        if not template_path.exists():
            console.print(f"[red]❌ 工作流模板不存在: {workflow}[/red]")
            console.print("\n💡 [yellow]下一步做什么？[/yellow]")
            console.print("  • 查看可用工作流: tradingflow serve 后在网页中选择模板")
            console.print("  • 或指定 Agent 手动组合: --agents fundamental,technical,sentiment")
            raise typer.Exit(1)
        workflow_def = json.loads(template_path.read_text(encoding="utf-8"))

    console.print(f"📋 工作流: [cyan]{workflow_def.get('name', workflow)}[/cyan]")
    agents_raw = workflow_def.get("agents", [])
    mode = workflow_def.get("mode", "parallel")
    if mode == "conditional":
        agent_names: list[str] = []
        for stage in workflow_def.get("stages", []):
            agent_names.extend(stage.get("agents", []))  # type: ignore[attr-defined]
    elif agents_raw and isinstance(agents_raw[0], str):
        agent_names = list(agents_raw)  # type: ignore[arg-type]
    else:
        agent_names = [a["role"] for a in agents_raw]  # type: ignore[index]
    console.print(f"👥 参与 Agent: {', '.join(agent_names)}\n")

    from backend.graph.builder import build_from_json

    with console.status("[bold green]正在分析中...", spinner="dots"):
        try:
            graph = build_from_json(workflow_def)
            result = asyncio.run(graph.ainvoke({
                "symbol": symbol,
                "market": market,
                "opinions": [],
                "final_report": None,
                "workflow_name": workflow_def.get("name", ""),
                "status": "running",
                "error": None,
                "round": 0,
                "selected_agents": [],
            }))
        except Exception as e:
            _show_analyze_error(e)
            raise typer.Exit(1)

    final_report = result.get("final_report")
    if not final_report:
        console.print("[red]❌ 未生成分析报告[/red]")
        raise typer.Exit(1)

    from backend.output.report import generate_markdown_report
    md_report = generate_markdown_report(final_report)

    if output:
        Path(output).write_text(md_report, encoding="utf-8")
        console.print(f"\n✅ 报告已保存到: [green]{output}[/green]")
    else:
        console.print("\n" + "=" * 60)
        console.print(Markdown(md_report))


def _show_analyze_error(exc: Exception):
    """将技术异常转为新手友好的中文提示 + 下一步行动"""

    # 隐藏 Python traceback，只显示友好信息
    console.print(f"\n[red]❌ 分析失败: {exc}[/red]\n")

    console.print(Panel.fit(
        "\n".join(_get_error_hints(exc)),
        title="💡 下一步做什么？",
        border_style="yellow",
        padding=(1, 2),
    ))


def _get_error_hints(exc: Exception) -> list[str]:
    """根据异常类型返回对应的解决提示"""
    msg = str(exc).lower()

    if "api_key" in msg or "api key" in msg or "unauthorized" in msg or "authentication" in msg:
        return [
            "🔑 [bold]API Key 缺失或无效[/bold]",
            "",
            "  [cyan]方案一（推荐）[/]: 注册 DeepSeek 获取免费额度",
            "    1. 访问 https://platform.deepseek.com 注册账号",
            "    2. 进入「API Keys」页面，点击「创建 API Key」",
            "    3. 复制密钥，在 .env 文件中修改:",
            "       LLM_API_KEY=你的密钥",
            "    4. 重新运行分析命令",
            "",
            "  [cyan]方案二[/]: 使用 Ollama 本地运行（无需联网和 API Key）",
            "    1. 安装 Ollama: https://ollama.com",
            "    2. 拉取模型: ollama pull qwen2.5:7b",
            "    3. 在 .env 中修改:",
            "       LLM_PROVIDER=ollama",
            "       LLM_API_KEY=ollama",
            "       LLM_MODEL=qwen2.5:7b",
            "       LLM_BASE_URL=http://localhost:11434/v1",
            "    4. 重新运行分析命令",
            "",
            "  🎓 [cyan]不想配置？[/]试试零配置演示: tradingflow demo",
        ]

    if "timeout" in msg or "timed out" in msg:
        return [
            "⏱️ [bold]分析超时[/bold]",
            "",
            "  可能原因：网络不稳定 或 分析的 Agent 太多",
            "",
            "  • 尝试减少 Agent: --agents fundamental,technical",
            "  • 增加超时时间: 在 .env 中设置 ANALYSIS_TIMEOUT=300",
            "  • 检查网络连接，确保能访问 LLM API 地址",
        ]

    if "connection" in msg or "connect" in msg or "refused" in msg or "name or service not known" in msg:
        return [
            "🌐 [bold]网络连接失败[/bold]",
            "",
            "  • 检查是否能访问 LLM API 地址",
            "  • 如果使用 Ollama，确认服务已启动: ollama serve",
            "  • 检查代理/VPN 设置",
            "  • 尝试切换模型提供商: LLM_PROVIDER=qwen",
        ]

    if "rate" in msg or "too many" in msg:
        return [
            "⏳ [bold]请求频率超限[/bold]",
            "",
            "  • API 请求太频繁，等 1-2 分钟后重试",
            "  • DeepSeek 免费额度每分钟限制约 60 次请求",
            "  • 减少 Agent 数量可以减少 API 调用",
        ]

    if "insufficient" in msg or "balance" in msg or "quota" in msg:
        return [
            "💰 [bold]API 额度不足[/bold]",
            "",
            "  • DeepSeek 免费额度已用完？充值或等次日重置",
            "  • 切换到其他模型: LLM_PROVIDER=qwen",
            "  • 使用 Ollama 本地运行，完全免费",
        ]

    return [
        f"⚠️ 分析过程遇到错误: {exc}",
        "",
        "  • 检查股票代码是否正确（A股 6 位，美股字母）",
        "  • 检查市场选择: -m a_share / -m h_stock / -m us_stock / -m bond / -m futures / -m crypto",
        "  • 检查 .env 中的 LLM 配置是否正确",
        "  • 查看日志: 设置 LOG_LEVEL=DEBUG 获取详细信息",
        "  • 🎓 试试零配置演示: tradingflow demo",
    ]


@app.command()
def search(
    keyword: str = typer.Argument(help="搜索关键词 (公司名、代码片段):茅台, 比亚迪, 00700"),
):
    """🔍 搜索股票代码 — 不确定代码时用它查找"""
    console.print(f"\n🔍 [bold]正在搜索: {keyword}[/bold]\n")

    try:
        from backend.core.discovery import auto_discover
        auto_discover()

        from backend.data.factory import get_provider
        provider = get_provider("a_share")

        results = provider.search_stock(keyword)
        if not results:
            results = provider.search_stock(keyword.lower())

        for extra_market in ("h_stock", "us_stock", "bond", "futures", "crypto"):
            if not results:
                try:
                    provider = get_provider(extra_market)
                    results = provider.search_stock(keyword)
                except Exception:
                    pass

        if not results:
            console.print("[yellow]⚠️ 未找到匹配的股票，请尝试其他关键词[/yellow]")
            console.print("  💡 提示: 可以试试 tradingflow demo 查看示例")
            return

        table = Table(title=f"搜索结果: \"{keyword}\"")
        table.add_column("代码", style="cyan")
        table.add_column("名称", style="green")
        table.add_column("市场", style="yellow")

        for r in results[:20]:
            code = r.get("code", r.get("symbol", ""))
            name = r.get("name", r.get("display_name", ""))
            market = r.get("market", "—")
            table.add_row(str(code), str(name), str(market))

        console.print(table)
        console.print(f"\n共找到 {len(results[:20])} 条结果\n")

        if len(results) >= 1:
            first = results[0]
            code = first.get("code", first.get("symbol", ""))
            market = first.get("market", "a_share")
            console.print(f"[dim]💡 快速分析: tradingflow analyze {code} -m {market}[/dim]")

    except ImportError:
        # 数据层不可用时，提供手动提示
        console.print("[yellow]⚠️ 数据层组件未安装或不可用[/yellow]")
        console.print("  📋 常见股票代码参考：")
        _print_common_stocks(keyword)

    except Exception as e:
        console.print(f"[yellow]⚠️ 搜索出错: {e}[/yellow]")
        console.print("  📋 以下为常见股票代码参考：")
        _print_common_stocks(keyword)


def _print_common_stocks(keyword: str):
    """打印常见股票代码参考"""
    kw = keyword.lower()
    common = [
        ("600519", "贵州茅台", "a_share"),
        ("000858", "五粮液", "a_share"),
        ("002594", "比亚迪", "a_share"),
        ("300750", "宁德时代", "a_share"),
        ("601318", "中国平安", "a_share"),
        ("600036", "招商银行", "a_share"),
        ("00700", "腾讯控股", "h_stock"),
        ("09988", "阿里巴巴-SW", "h_stock"),
        ("AAPL", "Apple Inc.", "us_stock"),
        ("MSFT", "Microsoft Corp.", "us_stock"),
        ("TSLA", "Tesla Inc.", "us_stock"),
        ("BTC", "Bitcoin", "crypto"),
        ("ETH", "Ethereum", "crypto"),
        ("IF2506", "沪深300期货", "futures"),
        ("511010", "国债ETF", "bond"),
    ]
    filtered = [(c, n, m) for c, n, m in common if kw in n.lower() or kw in c.lower()]
    if not filtered:
        filtered = common

    for code, name, mkt in filtered[:10]:
        market_label = {"a_share": "A股", "h_stock": "港股", "us_stock": "美股", "bond": "债券", "futures": "期货", "crypto": "加密货币"}.get(mkt, mkt)
        console.print(f"  [cyan]{code}[/] — {name} ({market_label})")


@app.command()
def config(
    key: str = typer.Argument("", help="配置项名称 (如: LLM_PROVIDER)"),
    value: str = typer.Argument("", help="配置项值"),
    show: bool = typer.Option(False, "--show", "-s", help="显示当前所有配置"),
):
    """查看或修改系统配置"""
    from backend.core.config import load_settings
    from backend.core.config_writer import update_setting

    if show:
        settings = load_settings()
        table = Table(title="当前配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")
        for field_name, field_value in settings.model_dump().items():
            display_val = str(field_value)
            if "key" in field_name.lower() and len(display_val) > 8:
                display_val = display_val[:4] + "****" + display_val[-4:]
            table.add_row(field_name, display_val)
        console.print(table)
        return

    if not key:
        console.print("[yellow]请指定配置项和值，或使用 --show 查看所有配置[/yellow]")
        raise typer.Exit(1)

    if not value:
        settings = load_settings()
        current = getattr(settings, key.lower(), "未找到")
        console.print(f"{key} = [green]{current}[/green]")
        return

    update_setting(key, value)
    console.print(f"✅ 已更新 [cyan]{key}[/cyan] = [green]{value}[/green]")


@app.command()
def skills(
    market: str = typer.Option("", "--market", "-m", help="按市场过滤"),
    category: str = typer.Option("", "--category", "-c", help="按类别过滤"),
):
    """列出所有可用的分析技能"""
    from backend.core.discovery import auto_discover
    auto_discover()

    from backend.skills.registry import list_skills

    skill_list = list_skills(market=market or None, category=category or None)

    table = Table(title="可用技能")
    table.add_column("名称", style="cyan")
    table.add_column("描述")
    table.add_column("类别", style="yellow")
    table.add_column("支持市场", style="green")

    for s in skill_list:
        table.add_row(s["name"], s["description"], s["category"], ", ".join(s["markets"]))

    console.print(table)
    console.print(f"\n共 {len(skill_list)} 个技能")


@app.command()
def agents_list():
    """列出所有可用的分析 Agent"""
    from backend.agents.registry import list_agents

    table = Table(title="可用 Agent")
    table.add_column("角色", style="cyan")
    table.add_column("名称")
    table.add_column("默认技能", style="yellow")

    for a in list_agents():
        table.add_row(a["role"], a["name"], ", ".join(a["default_skills"]))

    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="API 服务地址"),
    port: int = typer.Option(8000, "--port", "-p", help="API 服务端口"),
    reload: bool = typer.Option(True, "--reload", help="开发模式自动重载"),
):
    """启动 Web API 服务（FastAPI + Uvicorn）"""
    import uvicorn
    console.print(f"🚀 启动 API 服务: http://{host}:{port}")
    console.print(f"📖 API 文档: http://{host}:{port}/docs")
    uvicorn.run("backend.main:app", host=host, port=port, reload=reload)