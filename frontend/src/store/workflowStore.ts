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
   * 从工作流模板加载画布
   * 布局：Input(最左) → Skills(中左) → Analysts(中间竖排) → Summarizer(右)
   */
  loadFromTemplate: (template) => {
    const { agents, skills } = get();
    const gap = 140;

    // 输入节点（最左侧）
    const inputNode: Node = {
      id: 'input',
      type: 'input',
      position: { x: 20, y: 120 },
      data: { label: '输入', symbol: '', market: 'a_share' },
    };

    // 收集所有技能（去重），从 store 的 skills 数组中查找真实的 category、description 和 label
    const skillMetaMap = new Map(skills.map((s) => [s.name, s]));
    const allSkills = new Map<string, { category: string; description: string; label: string }>();
    template.agents.forEach((role) => {
      const agent = agents.find((a) => a.role === role);
      (agent?.current_skills || []).forEach((sk) => {
        if (!allSkills.has(sk)) {
          const meta = skillMetaMap.get(sk);
          allSkills.set(sk, {
            category: meta?.category || 'general',
            description: meta?.description || sk,
            label: meta?.label || sk,
          });
        }
      });
    });

    // 技能节点（竖排在分析师左侧）
    const skillNames = Array.from(allSkills.keys());
    const skillNodes: Node[] = skillNames.map((sk, i) => ({
      id: `skill_${sk}`,
      type: 'skill',
      position: { x: 400, y: 20 + i * 70 },
      data: { skillName: sk, label: allSkills.get(sk)!.label, category: allSkills.get(sk)!.category, description: allSkills.get(sk)!.description, params: {} },
    }));

    // 分析师节点竖排（中间）— 排除 trading，它放在总结之后
    const analystRoles = template.agents.filter((r) => r !== 'trading');
    const analystNodes: Node[] = analystRoles.map((role, i) => {
      const agent = agents.find((a) => a.role === role);
      return {
        id: role,
        type: 'analyst',
        position: { x: 760, y: 60 + i * gap },
        data: { role, label: agent?.name || role, skills: agent?.current_skills || [] },
      };
    });

    // 总结研判节点
    const totalHeight = (analystRoles.length - 1) * gap;
    const summarizerNode: Node = {
      id: 'summarizer',
      type: 'summarizer',
      position: { x: 1120, y: 60 + totalHeight / 2 },
      data: { role: 'summarizer', label: '总结研判', skills: [] },
    };

    // 交易执行节点（总结之后，最右侧）
    const tradingRole = template.agents.find((r) => r === 'trading');
    let tradingNode: Node | null = null;
    if (tradingRole) {
      const agent = agents.find((a) => a.role === tradingRole);
      tradingNode = {
        id: tradingRole,
        type: 'trading',
        position: { x: 1480, y: 60 + totalHeight / 2 },
        data: { role: tradingRole, label: agent?.name || '交易员', skills: agent?.current_skills || [] },
      };
    }

    // 边：Input → 每个 Analyst
    const inputEdges: Edge[] = template.agents.map((role) => ({
      id: `input-${role}`,
      source: 'input',
      target: role,
      sourceHandle: 'right',
      targetHandle: 'left',
    }));

    // 边：每个 Agent 的 Skill → 该 Agent
    const skillEdges: Edge[] = [];
    template.agents.forEach((role) => {
      const agent = agents.find((a) => a.role === role);
      (agent?.current_skills || []).forEach((sk) => {
        skillEdges.push({
          id: `skill_${sk}-${role}`,
          source: `skill_${sk}`,
          target: role,
          sourceHandle: 'right',
          targetHandle: 'left',
        });
      });
    });

    // 边：每个 Analyst → Summarizer
    const summaryEdges: Edge[] = analystRoles.map((role) => ({
      id: `${role}-summarizer`,
      source: role,
      target: 'summarizer',
      sourceHandle: 'right',
      targetHandle: 'left',
    }));

    // 边：Summarizer → Trading（如果存在交易节点）
    const tradingEdges: Edge[] = tradingNode ? [{
      id: 'summarizer-trading',
      source: 'summarizer',
      target: 'trading',
      sourceHandle: 'right',
      targetHandle: 'left',
    }] : [];

    // 收集所有需要的技能节点（仅分析师引用的）
    const neededSkillNames = new Set<string>();
    analystRoles.forEach((role) => {
      const agent = agents.find((a) => a.role === role);
      (agent?.current_skills || []).forEach((sk) => neededSkillNames.add(sk));
    });

    set({
      nodes: [inputNode, ...skillNodes.filter((n) => neededSkillNames.has((n.data as any).skillName)), ...analystNodes, summarizerNode, ...(tradingNode ? [tradingNode] : [])],
      edges: [...inputEdges, ...skillEdges, ...summaryEdges, ...tradingEdges],
    });
  },

  /** 从当前画布节点构建工作流定义 */
  _buildWorkflowDefinition: (name: string) => {
    const { nodes } = get();
    const agentNodes = nodes.filter((n) => n.type === 'analyst' || n.type === 'trading');
    const skillNodes = nodes.filter((n) => n.type === 'skill');
    const inputNode = nodes.find((n) => n.type === 'input');
    const configNode = nodes.find((n) => n.type === 'config');
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
      skills: skillNodes.map((n) => {
        const d = n.data as any;
        return { name: d.skillName, category: d.category, params: d.params || {} };
      }),
      input: inputNode ? { symbol: (inputNode.data as any).symbol, market: (inputNode.data as any).market } : undefined,
      config: configNode ? { period: (configNode.data as any).period, days: (configNode.data as any).days } : undefined,
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
