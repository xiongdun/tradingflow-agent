// frontend/src/constants/theme.ts
// 共享主题常量 — Agent 角色颜色映射，消除跨组件重复定义

/** 各 Agent 角色对应的主色调 */
export const STANCE_COLORS: Record<string, string> = {
  fundamental: '#10b981',      // 基本面 — 绿色
  technical: '#3b82f6',        // 技术面 — 蓝色
  sentiment: '#f59e0b',        // 情绪面 — 黄色
  news: '#8b5cf6',             // 新闻面 — 紫色
  macro: '#06b6d4',            // 宏观面 — 青色
  hot_money: '#ef4444',        // 游资/资金面 — 红色
  sector_rotation: '#ec4899',  // 板块轮动 — 粉色
  quant: '#14b8a6',            // 量化 — 青绿
  risk: '#f97316',             // 风控 — 橙色
};
