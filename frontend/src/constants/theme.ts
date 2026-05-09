// frontend/src/constants/theme.ts
// 共享主题常量 — Agent 角色颜色映射，节点类型颜色，消除跨组件重复定义

/** 各 Agent 角色对应的 macOS 风格色调 */
export const STANCE_COLORS: Record<string, string> = {
  fundamental: '#34C759',      // 基本面 — Apple Green
  technical: '#007AFF',        // 技术面 — Apple Blue
  sentiment: '#FF9500',        // 情绪面 — Apple Orange
  news: '#AF52DE',             // 新闻面 — Apple Purple
  macro: '#5AC8FA',            // 宏观面 — Apple Teal
  hot_money: '#FF3B30',        // 游资/资金面 — Apple Red
  sector_rotation: '#FF2D55',  // 板块轮动 — Apple Pink
  quant: '#64D2FF',            // 量化 — Apple Cyan
  risk: '#FFCC00',             // 风控 — Apple Yellow
  trading: '#FF6B35',          // 交易执行 — Orange Red
};

/** 各节点类型的边框/图标颜色 */
export const NODE_TYPE_COLORS: Record<string, string> = {
  analyst: '#007AFF',
  summarizer: '#AF52DE',
  input: '#34C759',
  skill: '#5AC8FA',
  config: '#FF9500',
  trading: '#FF6B35',
  adapter: '#FF2D55',          // 适配器 — Hot Pink
  event_trigger: '#FFCC00',    // 事件触发 — Yellow
  condition: '#64D2FF',        // 条件分支 — Cyan
  loop: '#30D158',             // 循环 — Green
};

/** 适配器类型 → 图标（AdapterNode / NodeConfig 共用） */
export const ADAPTER_ICONS: Record<string, string> = {
  http: '🌐', script: '📜', docker: '🐳',
  mcp: '🔌', langchain: '🦜', function: 'λ',
};

/** 事件类型 → 图标（EventTriggerNode / NodeConfig 共用） */
export const EVENT_ICONS: Record<string, string> = {
  price_alert: '🔔', indicator_signal: '📊', news_event: '📰', custom: '⚡',
};

/** 技能类别 → 颜色映射（SkillNode / Sidebar 共用） */
export const CATEGORY_COLORS: Record<string, string> = {
  fundamental: '#34C759',
  technical: '#007AFF',
  sentiment: '#FF9500',
  news: '#AF52DE',
  macro: '#5AC8FA',
  data: '#8e8e93',
  sector: '#FF2D55',
  flow: '#FF3B30',
  analysis: '#64D2FF',
  trading: '#FF6B35',
  general: '#8e8e93',
};

/** 技能类别 → 图标（SkillNode / NodeConfig 共用） */
export const CATEGORY_ICONS: Record<string, string> = {
  fundamental: '📊', technical: '📈', sentiment: '🔥',
  news: '📰', macro: '🌐', data: '💾',
  sector: '🔄', flow: '💧', analysis: '🔬',
  trading: '💹', general: '⚙️',
};
