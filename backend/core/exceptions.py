# backend/core/exceptions.py
# 项目自定义异常层级 — 统一错误处理


class VibeError(Exception):
    """项目基础异常"""


class DataFetchError(VibeError):
    """数据获取失败"""
    def __init__(self, provider: str, symbol: str, detail: str = ""):
        self.provider = provider
        self.symbol = symbol
        super().__init__(f"[{provider}] 获取 {symbol} 数据失败: {detail}")


class SkillExecutionError(VibeError):
    """技能执行失败"""
    def __init__(self, skill_name: str, detail: str = ""):
        self.skill_name = skill_name
        super().__init__(f"技能 '{skill_name}' 执行失败: {detail}")


class WorkflowBuildError(VibeError):
    """工作流构建失败"""
    def __init__(self, detail: str = ""):
        super().__init__(f"工作流构建失败: {detail}")


class AnalysisError(VibeError):
    """分析执行失败"""
    def __init__(self, symbol: str, detail: str = ""):
        self.symbol = symbol
        super().__init__(f"分析 {symbol} 失败: {detail}")


class ConfigError(VibeError):
    """配置错误"""
    pass
