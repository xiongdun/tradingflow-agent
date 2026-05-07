// frontend/src/types/index.ts
// 全局 TypeScript 类型定义 — Agent、技能、工作流、分析报告、配置、WebSocket 消息

// ─── Agent 与技能类型 ───

/** Agent 信息 — 后端注册的分析师角色 */
export interface AgentInfo {
  role: string;                // Agent 角色标识（如 fundamental、technical）
  name: string;                // 显示名称（如 "基本面分析师"）
  default_skills: string[];    // 默认技能列表
  current_skills: string[];    // 当前已配置的技能
  available_skills: string[];  // 可选技能列表
}

/** 技能信息 — 后端注册的分析技能 */
export interface SkillInfo {
  name: string;                // 技能名称（如 financial_data）
  description: string;         // 技能描述
  markets: string[];           // 支持的市场列表
  category: string;            // 所属类别（如 fundamental、technical）
  params?: Record<string, string>;  // 参数说明
  depends_on?: string[];       // 依赖的其他技能
}

// ─── 流程节点数据类型 ───

/** 输入节点数据 — 股票代码 + 市场 */
export interface InputNodeData {
  symbol: string;              // 股票代码
  market: string;              // 市场类型
  label: string;
}

/** 配置节点数据 — 分析参数 */
export interface ConfigNodeData {
  period: string;              // K线周期 daily/weekly/monthly
  days: number;                // 历史天数
  label: string;
}

/** 技能节点数据 — 挂载到画布上的技能 */
export interface SkillNodeData {
  skillName: string;           // 技能标识
  label: string;               // 显示名称
  category: string;            // 技能类别
  description: string;         // 技能描述
  params: Record<string, string>;
}

// ─── 工作流类型 ───

/** 工作流画布节点 — React Flow 节点数据结构 */
export interface WorkflowNode {
  id: string;                  // 节点唯一标识
  type: 'analyst' | 'summarizer' | 'input' | 'skill' | 'config';  // 节点类型
  data: {
    role?: string;             // Agent 角色（analyst 节点）
    label: string;             // 显示标签
    skills?: string[];         // 已选技能列表（analyst 节点）
    extra_prompt?: string;     // 额外提示词
    skillName?: string;        // 技能标识（skill 节点）
    category?: string;         // 技能类别
    symbol?: string;           // 股票代码（input 节点）
    market?: string;           // 市场类型（input 节点）
    period?: string;           // K线周期（config 节点）
    days?: number;             // 历史天数（config 节点）
  };
  position: { x: number; y: number };  // 画布坐标
}

/** 工作流画布边 — 连接两个节点的有向边 */
export interface WorkflowEdge {
  id: string;                  // 边唯一标识
  source: string;              // 源节点 ID
  target: string;              // 目标节点 ID
}

/** 工作流定义 — 保存/加载的工作流结构 */
export interface WorkflowDefinition {
  name: string;                // 工作流名称
  description?: string;        // 描述
  agents: Array<{
    role: string;              // Agent 角色
    skills?: string[];         // 自定义技能（可选，覆盖默认）
    extra_prompt?: string;     // 额外提示词
  }>;
  skills?: Array<{             // 独立技能节点
    name: string;
    category: string;
    params?: Record<string, string>;
  }>;
  input?: {                    // 输入节点配置
    symbol?: string;
    market?: string;
  };
  config?: {                   // 配置节点
    period?: string;
    days?: number;
  };
  summarizer_prompt?: string;  // 总结 Agent 的自定义提示词
}

/** 工作流模板 — 后端预置的工作流模板 */
export interface WorkflowTemplate {
  id: string;                  // 模板 ID（对应文件名）
  name: string;                // 模板名称
  description: string;         // 模板描述
  agents: string[];            // 包含的 Agent 角色列表
}

// ─── 分析结果类型 ───

/** 分析师意见 — 单个 Agent 的分析输出 */
export interface AgentOpinion {
  agent_name: string;          // 分析师名称
  agent_role: string;          // 分析师角色
  stock: string;               // 股票代码
  market: string;              // 市场类型
  stance: 'bullish' | 'bearish' | 'neutral';  // 立场：看多/看空/中性
  confidence: number;          // 置信度（0-1）
  key_points: string[];        // 核心论点列表
  risk_factors: string[];      // 风险因素列表
  summary: string;             // 分析总结
  data_evidence: Record<string, unknown>;  // 数据证据
}

/** 最终分析报告 — 总结 Agent 的综合研判结果 */
export interface FinalReport {
  stock: string;               // 股票代码
  market: string;              // 市场类型
  overall_stance: 'bullish' | 'bearish' | 'neutral';  // 整体立场
  overall_confidence: number;  // 整体置信度（0-1）
  consensus_points: string[];  // 分析师共识观点
  disagreement_points: string[];  // 分歧观点
  key_risks: string[];         // 关键风险
  opportunities: string[];     // 投资机会
  action_suggestion: 'buy' | 'sell' | 'hold' | 'watch';  // 投资建议
  summary: string;             // 综合分析总结
  agent_opinions: AgentOpinion[];  // 各分析师意见列表
}

// ─── 系统配置类型 ───

/** 应用配置 — 对应后端 Settings 模型 */
export interface AppConfig {
  llm_provider: string;        // LLM 提供商（openai/deepseek/qwen 等）
  llm_model: string;           // 模型名称
  llm_api_key: string;         // API 密钥（脱敏显示）
  llm_base_url: string;        // API 基础 URL
  llm_temperature: number;     // 生成温度
  llm_max_tokens: number;      // 最大 token 数
  default_market: string;      // 默认市场
  analysis_timeout: number;    // 分析超时时间（秒）
  api_host: string;            // API 服务地址
  api_port: number;            // API 服务端口
  log_level: string;           // 日志级别
  color_scheme: string;        // 涨跌颜色方案：cn=红涨绿跌，international=绿涨红跌
}

// ─── WebSocket 消息类型 ───

/** WebSocket 消息 — 后端推送的实时消息协议 */
export interface WSMessage {
  type: 'status' | 'opinion' | 'report' | 'error' | 'agent_status';  // 消息类型
  status?: string;             // 状态值（started/running/completed）
  agents?: string[];           // 参与分析的 Agent 列表
  workflow?: string;           // 工作流名称
  data?: unknown;              // 消息数据（opinion 或 report）
  report?: FinalReport;        // 最终报告
  markdown?: string;           // Markdown 格式报告
  message?: string;            // 错误消息
  agent_role?: string;          // Agent 角色（agent_status 消息用）
  agent_name?: string;          // Agent 名称
  skill?: string;               // 技能名称（skill_done 消息用）
}
