# backend/plugins/manifest.py
# 插件清单模型 — 统一的插件自描述格式，支持技能/适配器/数据源/Agent

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# 插件安装根目录 — 所有插件子模块共享此常量，避免重复定义
PLUGINS_DIR = Path(__file__).parent.parent / "data" / "plugins"


class PluginType(str, Enum):
    """插件类型枚举"""
    SKILL = "skill"              # 数据技能
    ADAPTER = "adapter"          # 外部项目适配器
    DATASOURCE = "datasource"    # 数据源 Provider
    AGENT = "agent"              # 分析 Agent
    WORKFLOW = "workflow"        # 工作流模板


class ParamSpec(BaseModel):
    """单个参数的规格说明"""
    type: str = "string"         # 参数类型: string/integer/float/boolean/array/object
    description: str = ""        # 参数描述
    required: bool = False       # 是否必填
    default: Any = None          # 默认值
    enum: list[Any] | None = None  # 可选值列表


class Permission(str, Enum):
    """插件权限枚举"""
    NETWORK = "network"          # 网络访问
    DATA_READ = "data_read"      # 读取本地数据
    DATA_WRITE = "data_write"    # 写入本地数据
    EXECUTE = "execute"          # 执行外部命令
    LLM_CALL = "llm_call"        # 调用 LLM API
    FULL_ACCESS = "full_access"  # 完全访问（仅本地可信插件）


class PluginManifest(BaseModel):
    """插件清单 — 插件的自描述元数据

    所有插件（技能、适配器、数据源、Agent）使用同一格式自描述。
    存储为插件目录下的 manifest.json 文件。
    """
    name: str                                    # 插件唯一标识符
    version: str = "1.0.0"                       # 语义化版本号
    type: PluginType = PluginType.SKILL          # 插件类型
    description: str = ""                        # 插件描述
    author: str = ""                             # 作者
    license: str = "MIT"                         # 开源许可证
    homepage: str = ""                           # 项目主页 URL

    # ── 功能声明 ──
    markets: list[str] = Field(default_factory=lambda: ["a_share", "h_stock", "us_stock"])
    category: str = "general"                    # 技能类别
    entry_point: str = ""                        # 入口函数: "module:function"
    dependencies: list[str] = Field(default_factory=list)  # 依赖的其他插件
    params: dict[str, ParamSpec] = Field(default_factory=dict)  # 参数规格

    # ── 适配器专用字段 ──
    adapter_type: str = ""                       # 适配器类型: mcp/http/script/docker/langchain/function
    adapter_config: dict[str, Any] = Field(default_factory=dict)  # 适配器默认配置
    input_schema: dict[str, Any] = Field(default_factory=dict)   # 输入状态 schema
    output_schema: dict[str, Any] = Field(default_factory=dict)  # 输出状态 schema

    # ── 安全 ──
    permissions: list[Permission] = Field(default_factory=list)  # 所需权限列表

    # ── 兼容性 ──
    min_platform_version: str = "0.1.0"          # 最低平台版本要求
    max_platform_version: str = ""               # 最高平台版本要求（空=不限）

    # ── 来源信息（安装时填充）──
    source: str = ""                             # 安装来源: local/git/pip/url/registry
    source_url: str = ""                         # 来源 URL
    installed_path: str = ""                     # 安装路径
    enabled: bool = True                         # 是否启用

    def to_skill_meta_kwargs(self) -> dict[str, Any]:
        """转换为 SkillMeta 构造参数（向后兼容现有技能系统）"""
        return {
            "name": self.name,
            "description": self.description,
            "markets": self.markets,
            "category": self.category,
            "params": {k: {"type": v.type, "description": v.description, "required": v.required}
                       for k, v in self.params.items()},
            "depends_on": self.dependencies,
            "label": self.description.split("—")[0].split("。")[0][:20] if self.description else self.name,
        }

    def validate_compatibility(self, platform_version: str) -> str | None:
        """校验平台版本兼容性，返回错误信息或 None"""
        from packaging.version import Version
        try:
            current = Version(platform_version)
            required = Version(self.min_platform_version)
            if current < required:
                return f"平台版本 {platform_version} 低于插件要求的最低版本 {self.min_platform_version}"
            if self.max_platform_version:
                max_ver = Version(self.max_platform_version)
                if current > max_ver:
                    return f"平台版本 {platform_version} 高于插件支持的最高版本 {self.max_platform_version}"
        except Exception:
            pass  # 版本解析失败时不做兼容性检查
        return None
