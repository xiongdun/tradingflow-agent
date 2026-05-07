// frontend/src/store/workflowStore.ts
// 全局状态管理 — 使用 Zustand 管理工作流画布、Agent/技能数据、分析状态

import { create } from 'zustand';
import { applyNodeChanges, applyEdgeChanges, type NodeChange, type EdgeChange, type Node, type Edge } from '@xyflow/react';
import type { AgentInfo, SkillInfo, FinalReport, AgentOpinion, WorkflowTemplate } from '../types';

/** Agent 执行进度 */
export interface AgentProgress {
  status: 'idle' | 'running' | 'done' | 'error';
  messages: string[];
  opinion?: AgentOpinion;
}

/** 工作流状态接口 — 定义全局状态和所有操作方法 */
interface WorkflowState {
  // ─── React Flow 画布状态 ───
  nodes: Node[];               // 画布节点列表
  edges: Edge[];               // 画布边列表

  // ─── 后端 API 数据 ───
  agents: AgentInfo[];         // 所有可用 Agent
  skills: SkillInfo[];         // 所有可用技能
  workflows: WorkflowTemplate[];  // 预置工作流模板

  // ─── 分析状态 ───
  selectedSymbol: string;      // 当前股票代码
  selectedMarket: string;      // 当前市场类型
  isAnalyzing: boolean;        // 是否正在分析
  analyzingAgents: string[];   // 正在分析中的 Agent 角色列表
  agentProgressMap: Record<string, AgentProgress>;  // 每个 Agent 的执行进度
  analysisProgress: string[];  // 分析进度消息列表
  opinions: AgentOpinion[];    // 已收到的分析师意见
  finalReport: FinalReport | null;  // 最终分析报告
  markdownReport: string;      // Markdown 格式报告

  // ─── 节点配置 ───
  selectedNodeId: string | null;  // 当前选中的节点 ID

  // ─── 操作方法 ───
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;  // React Flow 节点变更回调
  onEdgesChange: (changes: EdgeChange[]) => void;  // React Flow 边变更回调
  addNode: (node: Node) => void;
  removeNode: (id: string) => void;
  updateNodeData: (id: string, data: Record<string, unknown>) => void;
  setAgents: (agents: AgentInfo[]) => void;
  setSkills: (skills: SkillInfo[]) => void;
  setWorkflows: (workflows: WorkflowTemplate[]) => void;
  setSelectedSymbol: (s: string) => void;
  setSelectedMarket: (m: string) => void;
  setAnalyzing: (v: boolean) => void;
  setAnalyzingAgents: (agents: string[]) => void;  // 设置分析中的 Agent 列表
  removeAnalyzingAgent: (role: string) => void;    // 移除单个已完成的 Agent
  setAgentProgress: (role: string, progress: Partial<AgentProgress>) => void;  // 更新单个 Agent 进度
  addProgress: (msg: string) => void;     // 添加进度消息
  addOpinion: (op: AgentOpinion) => void; // 添加分析师意见
  setFinalReport: (r: FinalReport | null, md?: string) => void;
  setSelectedNodeId: (id: string | null) => void;
  resetAnalysis: () => void;              // 重置所有分析状态
  loadFromTemplate: (template: WorkflowTemplate) => void;  // 从模板加载工作流
  saveWorkflow: (name: string) => Promise<void>;  // 保存当前画布为工作流模板
  exportWorkflow: () => void;            // 导出当前画布为 JSON 文件下载
}

/** 全局状态 Store — 使用 Zustand create 创建 */
export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // 初始状态
  nodes: [],
  edges: [],
  agents: [],
  skills: [],
  workflows: [],
  selectedSymbol: '',
  selectedMarket: 'a_share',
  isAnalyzing: false,
  analyzingAgents: [],
  agentProgressMap: {},
  analysisProgress: [],
  opinions: [],
  finalReport: null,
  markdownReport: '',
  selectedNodeId: null,

  // ─── 画布操作 ───
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  /** 应用 React Flow 节点变更（位置移动、删除、选中等） */
  onNodesChange: (changes) => {
    const { nodes } = get();
    const next = applyNodeChanges(changes as NodeChange[], nodes);
    set({ nodes: next });
  },

  /** 应用 React Flow 边变更（删除等） */
  onEdgesChange: (changes) => {
    const { edges } = get();
    const next = applyEdgeChanges(changes as EdgeChange[], edges);
    set({ edges: next });
  },

  /** 添加新节点到画布 */
  addNode: (node) => set((s) => ({ nodes: [...s.nodes, node] })),
  /** 从画布移除指定节点 */
  removeNode: (id) => set((s) => ({ nodes: s.nodes.filter((n) => n.id !== id) })),

  /** 更新指定节点的数据（技能、额外提示词等） */
  updateNodeData: (id, data) => set((s) => ({
    nodes: s.nodes.map((n) => n.id === id ? { ...n, data: { ...n.data, ...data } } : n),
  })),

  // ─── API 数据设置 ───
  setAgents: (agents) => set({ agents }),
  setSkills: (skills) => set({ skills }),
  setWorkflows: (workflows) => set({ workflows }),

  // ─── 分析控制 ───
  setSelectedSymbol: (s) => set({ selectedSymbol: s }),
  setSelectedMarket: (m) => set({ selectedMarket: m }),
  setAnalyzing: (v) => set({ isAnalyzing: v }),
  setAnalyzingAgents: (agents) => set({ analyzingAgents: agents }),
  removeAnalyzingAgent: (role) => set((s) => ({ analyzingAgents: s.analyzingAgents.filter((r) => r !== role) })),
  setAgentProgress: (role, progress) => set((s) => ({
    agentProgressMap: {
      ...s.agentProgressMap,
      [role]: { ...s.agentProgressMap[role], status: 'idle', messages: [], ...progress },
    },
  })),
  addProgress: (msg) => set((s) => ({ analysisProgress: [...s.analysisProgress, msg] })),
  addOpinion: (op) => set((s) => ({ opinions: [...s.opinions, op] })),
  setFinalReport: (r, md = '') => set({ finalReport: r, markdownReport: md }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),

  /** 重置所有分析状态（清空意见、报告、进度） */
  resetAnalysis: () => set({ opinions: [], finalReport: null, markdownReport: '', analysisProgress: [], isAnalyzing: false, analyzingAgents: [], agentProgressMap: {} }),

  /**
   * 从工作流模板加载画布 — 生成分析师节点 + 总结节点 + 连接边
   * 布局：每行 3 个分析师节点，总结节点在下方居中
   */
  loadFromTemplate: (template) => {
    const { agents } = get();
    // 为每个 Agent 角色创建画布节点，按网格排列
    const analystNodes: Node[] = template.agents.map((role, i) => {
      const agent = agents.find((a) => a.role === role);
      return {
        id: role,
        type: 'analyst',
        position: { x: 100 + (i % 3) * 280, y: 100 + Math.floor(i / 3) * 200 },
        data: { role, label: agent?.name || role, skills: agent?.current_skills || [] },
      };
    });
    // 创建总结研判节点，放在分析师下方
    const summarizerNode: Node = {
      id: 'summarizer',
      type: 'summarizer',
      position: { x: 100 + (template.agents.length % 3) * 280, y: 100 + Math.floor(template.agents.length / 3) * 200 + 200 },
      data: { role: 'summarizer', label: '总结研判', skills: [] },
    };
    // 创建从每个分析师到总结节点的连接边
    const edges: Edge[] = template.agents.map((role) => ({
      id: `${role}-summarizer`,
      source: role,
      target: 'summarizer',
    }));
    set({ nodes: [...analystNodes, summarizerNode], edges });
  },

  /** 从当前画布节点构建工作流定义 */
  _buildWorkflowDefinition: (name: string) => {
    const { nodes } = get();
    const agentNodes = nodes.filter((n) => n.type === 'analyst');
    return {
      name,
      description: '',
      agents: agentNodes.map((n) => {
        const d = n.data as any;
        const entry: Record<string, unknown> = { role: d.role };
        if (d.skills?.length) entry.skills = d.skills;
        if (d.extra_prompt) entry.extra_prompt = d.extra_prompt;
        if (d.label && d.label !== d.role) entry.name = d.label;
        return entry;
      }),
      summarizer_prompt: '',
    };
  },

  /** 保存当前画布为工作流模板 — 调用后端 API 持久化为 JSON 文件 */
  saveWorkflow: async (name: string) => {
    const definition = get()._buildWorkflowDefinition(name);
    const resp = await fetch('/api/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, definition }),
    });
    if (!resp.ok) throw new Error('保存失败');
  },

  /** 导出当前画布为 JSON 文件 — 触发浏览器下载 */
  exportWorkflow: () => {
    const definition = get()._buildWorkflowDefinition('自定义工作流');
    const blob = new Blob([JSON.stringify(definition, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${definition.name}.json`;
    a.click();
    URL.revokeObjectURL(url);
  },
}));
