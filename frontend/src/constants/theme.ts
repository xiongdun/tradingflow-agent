// frontend/src/constants/theme.ts
// 共享主题常量 — Agent 角色颜色映射，消除跨组件重复定义

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
