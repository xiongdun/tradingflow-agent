// frontend/src/api/client.ts
// API 客户端 — 封装所有后端 REST API 调用，统一错误处理

import type { AgentInfo, SkillInfo, WorkflowTemplate, AppConfig, FinalReport } from '../types';

// API 基础路径
const BASE = '/api';

/**
 * 通用 JSON 请求封装 — 自动设置 Content-Type 并检查响应状态
 * @param url 请求地址
 * @param init fetch 选项（method、body 等）
 * @returns 解析后的 JSON 数据
 */
async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ─── Agent 管理 API ───

/** 获取所有 Agent 列表 */
export const getAgents = () => fetchJSON<AgentInfo[]>(`${BASE}/agents`);
/** 获取指定 Agent 的当前技能列表 */
export const getAgentSkills = (role: string) => fetchJSON<{ role: string; skills: string[] }>(`${BASE}/agents/${role}/skills`);
/** 批量替换 Agent 的技能列表 */
export const setAgentSkills = (role: string, skills: string[]) => fetchJSON<{ status: string }>(`${BASE}/agents/${role}/skills`, { method: 'PUT', body: JSON.stringify({ skills }) });
/** 为 Agent 添加单个技能 */
export const addAgentSkill = (role: string, skill: string) => fetchJSON<{ status: string; skills: string[] }>(`${BASE}/agents/${role}/skills/add`, { method: 'POST', body: JSON.stringify({ skill }) });
/** 移除 Agent 的单个技能 */
export const removeAgentSkill = (role: string, skill: string) => fetchJSON<{ status: string; skills: string[] }>(`${BASE}/agents/${role}/skills/remove`, { method: 'POST', body: JSON.stringify({ skill }) });
/** 将 Agent 的技能重置为默认配置 */
export const resetAgentSkills = (role: string) => fetchJSON<{ status: string; skills: string[] }>(`${BASE}/agents/${role}/skills/reset`, { method: 'POST' });

// ─── 技能与工作流 API ───

/** 获取所有可用技能，支持按市场和类别过滤 */
export const getSkills = (market?: string, category?: string) => { const p = new URLSearchParams(); if (market) p.set('market', market); if (category) p.set('category', category); return fetchJSON<SkillInfo[]>(`${BASE}/skills?${p}`); };
/** 获取所有预置工作流模板 */
export const getWorkflows = () => fetchJSON<WorkflowTemplate[]>(`${BASE}/workflows`);

// ─── 股票分析 API ───

/** 运行股票分析（REST 同步模式，返回完整报告） */
export const runAnalysis = (symbol: string, market: string, workflow: string, agents?: string[]) =>
  fetchJSON<{ status: string; report?: FinalReport; markdown?: string; error?: string }>(`${BASE}/analyze`, { method: 'POST', body: JSON.stringify({ symbol, market, workflow, agents }) });

// ─── 系统配置 API ───

/** 获取当前系统配置（API Key 脱敏） */
export const getConfig = () => fetchJSON<AppConfig>(`${BASE}/config`);
/** 更新单个配置项 */
export const updateConfig = (key: string, value: string) => fetchJSON<{ status: string }>(`${BASE}/config`, { method: 'POST', body: JSON.stringify({ key, value }) });

// ─── 行情数据 API ───

/** 获取 K 线数据，格式化为 TradingView Lightweight Charts 可用格式 */
export const getKline = (symbol: string, market: string, period = 'daily', days = 120) =>
  fetchJSON<{ symbol: string; bars: Array<{ time: string; open: number; high: number; low: number; close: number; volume?: number }> }>(
    `${BASE}/market/kline`, { method: 'POST', body: JSON.stringify({ symbol, market, period, days }) }
  );

/** 将分析师意见转换为图表买卖信号标记 */
export const getMarkers = (symbol: string, market: string, opinions: any[]) =>
  fetchJSON<{ markers: any[]; opinion_lines: any[] }>(
    `${BASE}/market/markers`, { method: 'POST', body: JSON.stringify({ symbol, market, opinions }) }
  );
