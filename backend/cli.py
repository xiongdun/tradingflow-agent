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

# 创建 Typer CLI 应用
app = typer.Typer(
    name="tradingflow",
    help="🤖 TradingFlow Agent — AI 多智能体股票分析系统",
    no_args_is_help=True,
)
console = Console()


@app.command()
def analyze(
    symbol: str = typer.Argument(help="股票代码 (如: 600519, AAPL)"),
    market: str = typer.Option("a_share", "--market", "-m", help="市场: a_share, h_stock, us_stock"),
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
            raise typer.Exit(1)
        workflow_def = json.loads(template_path.read_text(encoding="utf-8"))

    console.print(f"📋 工作流: [cyan]{workflow_def.get('name', workflow)}[/cyan]")
    # 提取 Agent 列表（兼容不同模板格式）
    agents_raw = workflow_def.get("agents", [])
    mode = workflow_def.get("mode", "parallel")
    if mode == "conditional":
        agent_names = []
        for stage in workflow_def.get("stages", []):
            agent_names.extend(stage.get("agents", []))
    elif agents_raw and isinstance(agents_raw[0], str):
        agent_names = agents_raw
    else:
        agent_names = [a["role"] for a in agents_raw]
    console.print(f"👥 参与 Agent: {', '.join(agent_names)}\n")

    # 构建并执行工作流
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
            console.print(f"[red]❌ 分析失败: {e}[/red]")
            raise typer.Exit(1)

    # 展示分析结果
    final_report = result.get("final_report")
    if not final_report:
        console.print("[red]❌ 未生成分析报告[/red]")
        raise typer.Exit(1)

    # 生成 Markdown 报告
    from backend.output.report import generate_markdown_report
    md_report = generate_markdown_report(final_report)

    if output:
        # 保存到文件
        Path(output).write_text(md_report, encoding="utf-8")
        console.print(f"\n✅ 报告已保存到: [green]{output}[/green]")
    else:
        # 直接打印到终端
        console.print("\n" + "=" * 60)
        console.print(Markdown(md_report))


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
        # 以表格形式展示所有配置项
        settings = load_settings()
        table = Table(title="当前配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")
        for field_name, field_value in settings.model_dump().items():
            # 脱敏处理 API Key
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
        # 查看单个配置项的当前值
        settings = load_settings()
        current = getattr(settings, key.lower(), "未找到")
        console.print(f"{key} = [green]{current}[/green]")
        return

    # 更新配置项
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

    # 以表格形式展示技能列表
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

    # 以表格形式展示 Agent 列表
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
