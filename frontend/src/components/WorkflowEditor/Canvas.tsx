// frontend/src/components/WorkflowEditor/Canvas.tsx
// 工作流画布 — React Flow 拖拽式画布，支持节点拖放、连线、缩放、小地图

import { useCallback, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useReactFlow,
  type Connection,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useWorkflowStore } from '../../store/workflowStore';
import { STANCE_COLORS } from '../../constants/theme';
import { AgentNode } from './AgentNode';
import { SummarizerNode } from './SummarizerNode';
import { SkillNode } from './SkillNode';
import { InputNode } from './InputNode';
import { ConfigNode } from './ConfigNode';
import { TradingNode } from './TradingNode';

// 注册所有自定义节点类型
const nodeTypes = {
  analyst: AgentNode,
  summarizer: SummarizerNode,
  skill: SkillNode,
  input: InputNode,
  config: ConfigNode,
  trading: TradingNode,
};

/** 连接规则：定义哪些节点类型之间允许连线 */
const CONNECTION_RULES: Record<string, string[]> = {
  input:      ['analyst', 'skill'],
  config:     ['skill'],
  skill:      ['analyst'],
  analyst:    ['summarizer'],
  summarizer: ['trading'],
  trading:    [],
};

/**
 * FlowCanvas — React Flow 画布核心组件
 */
function FlowCanvas() {
  const {
    nodes, edges, setEdges, onNodesChange, onEdgesChange,
    addNode, setSelectedNodeId, updateNodeData, agents, skills,
  } = useWorkflowStore();
  const reactFlow = useReactFlow();
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  /** 连线回调 — skill→analyst 连线时自动将 skill 加入 analyst 的 skills 列表 */
  const onConnect = useCallback(
    (conn: Connection) => {
      if (conn.source && conn.target) {
        setEdges([...edges, {
          id: `${conn.source}-${conn.target}`,
          source: conn.source,
          target: conn.target,
          sourceHandle: conn.sourceHandle,
          targetHandle: conn.targetHandle,
        }]);

        // skill → analyst/trading：将 skill 名称加入目标节点的 skills 列表
        const sourceNode = nodes.find((n) => n.id === conn.source);
        const targetNode = nodes.find((n) => n.id === conn.target);
        if (sourceNode?.type === 'skill' && (targetNode?.type === 'analyst' || targetNode?.type === 'trading')) {
          const skillName = (sourceNode.data as any).skillName;
          const currentSkills: string[] = (targetNode.data as any).skills || [];
          if (skillName && !currentSkills.includes(skillName)) {
            updateNodeData(targetNode.id, { skills: [...currentSkills, skillName] });
          }
        }
      }
    },
    [edges, setEdges, nodes, updateNodeData],
  );

  /** 连接验证 */
  const isValidConnection = useCallback(
    (conn: Connection) => {
      if (!conn.source || !conn.target) return false;
      const sourceNode = nodes.find((n) => n.id === conn.source);
      const targetNode = nodes.find((n) => n.id === conn.target);
      if (!sourceNode || !targetNode) return false;
      const allowed = CONNECTION_RULES[sourceNode.type as string] || [];
      return allowed.includes(targetNode.type as string);
    },
    [nodes],
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  /** 拖放回调 — 使用 getState() 避免闭包过期 */
  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const raw = e.dataTransfer.getData('application/reactflow');
      if (!raw) return;

      // 始终读取最新 store 状态，避免闭包中 nodes/agents/skills 过期
      const state = useWorkflowStore.getState();
      const currentNodes = state.nodes;
      const currentAgents = state.agents;
      const currentSkills = state.skills;

      const parts = raw.split(':');
      const nodeType = parts[0];
      const id = parts[1] || nodeType;
      const label = parts[2] || id;

      if (['input', 'summarizer', 'config'].includes(nodeType) && currentNodes.some((n) => n.type === nodeType)) return;
      if (currentNodes.some((n) => n.id === id)) return;

      const bounds = (e.target as HTMLElement).getBoundingClientRect();
      const position = reactFlow.screenToFlowPosition({
        x: e.clientX - bounds.left,
        y: e.clientY - bounds.top,
      });

      if (nodeType === 'analyst') {
        const agent = currentAgents.find((a) => a.role === id);
        const agentSkills = agent?.current_skills || [];

        // 批量构建所有节点和边，一次性写入 store
        const batchNodes: any[] = [];
        const batchEdges: typeof state.edges = [];

        // Analyst 节点
        batchNodes.push({
          id,
          type: 'analyst',
          position,
          data: { role: id, label: agent?.name || label, skills: agentSkills },
        });

        // Skill 节点（垂直居中排列在 Analyst 左侧 200px）
        const skillGap = 64;
        const startY = position.y - ((agentSkills.length - 1) * skillGap) / 2;
        agentSkills.forEach((skName, i) => {
          const nodeId = `skill_${skName}`;
          if (!currentNodes.some((n) => n.id === nodeId)) {
            const skMeta = currentSkills.find((s) => s.name === skName);
            batchNodes.push({
              id: nodeId,
              type: 'skill',
              position: { x: position.x - 200, y: startY + i * skillGap },
              data: {
                skillName: skName,
                label: skMeta?.label || skName,
                category: skMeta?.category || 'general',
                description: skMeta?.description || skName,
                params: {},
              },
            });
          }
          batchEdges.push({
            id: `${nodeId}-${id}`,
            source: nodeId,
            target: id,
            sourceHandle: 'right',
            targetHandle: 'left',
          });
        });

        // 一次性原子写入
        useWorkflowStore.setState((s) => ({
          nodes: [...s.nodes, ...batchNodes],
          edges: [...s.edges, ...batchEdges],
        }));
      } else if (nodeType === 'summarizer') {
        addNode({
          id: 'summarizer',
          type: 'summarizer',
          position,
          data: { role: 'summarizer', label: '总结研判', skills: [] },
        });
      } else if (nodeType === 'skill') {
        addNode({
          id,
          type: 'skill',
          position,
          data: {
            skillName: id,
            label,
            category: parts[3] || 'general',
            description: parts[4] || '',
            params: {},
          },
        });
      } else if (nodeType === 'input') {
        addNode({
          id: 'input',
          type: 'input',
          position,
          data: { label: '输入', symbol: '', market: 'a_share' },
        });
      } else if (nodeType === 'config') {
        addNode({
          id: 'config',
          type: 'config',
          position,
          data: { label: '参数配置', period: 'daily', days: 120 },
        });
      }
    },
    [reactFlow, addNode],
  );

  /** 边变更回调 — 删除 skill→analyst 边时同步移除 analyst 的 skill */
  const handleEdgesChange = useCallback(
    (changes: any[]) => {
      // 检测删除的边
      changes.forEach((c: any) => {
        if (c.type === 'remove') {
          const edge = edges.find((e) => e.id === c.id);
          if (edge) {
            const src = nodes.find((n) => n.id === edge.source);
            const tgt = nodes.find((n) => n.id === edge.target);
            if (src?.type === 'skill' && (tgt?.type === 'analyst' || tgt?.type === 'trading')) {
              const skillName = (src.data as any).skillName;
              const currentSkills: string[] = (tgt.data as any).skills || [];
              if (skillName && currentSkills.includes(skillName)) {
                updateNodeData(tgt.id, { skills: currentSkills.filter((s) => s !== skillName) });
              }
            }
          }
        }
      });
      onEdgesChange(changes);
    },
    [edges, nodes, onEdgesChange, updateNodeData],
  );

  const onNodeClick = useCallback((_: any, node: any) => {
    setSelectedNodeId(node.id);
    setSelectedEdgeId(null);
  }, [setSelectedNodeId]);

  const onEdgeClick = useCallback((_: any, edge: any) => {
    setSelectedEdgeId(edge.id);
    setSelectedNodeId(null);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
  }, []);

  // 为每条边设置 inline style：skill→agent 用虚线，其余实线，选中高亮
  const styledEdges = edges.map((e) => {
    const srcNode = nodes.find((n) => n.id === e.source);
    const isSkillEdge = srcNode?.type === 'skill';
    const isSelected = e.id === selectedEdgeId;
    return {
      ...e,
      selected: isSelected,
      style: {
        stroke: isSelected ? '#6366f1' : 'rgba(120,160,255,0.35)',
        strokeWidth: isSelected ? 3 : 2,
        filter: isSelected ? 'drop-shadow(0 0 6px rgba(99,102,241,0.6))' : 'none',
        transition: 'stroke 0.2s, stroke-width 0.2s, filter 0.2s',
        ...(isSkillEdge ? { strokeDasharray: '6 4' } : {}),
      },
    };
  });

  return (
    <ReactFlow
      nodes={nodes}
      edges={styledEdges}
      onNodesChange={onNodesChange}
      onEdgesChange={handleEdgesChange}
      onConnect={onConnect}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onNodeClick={onNodeClick}
      onEdgeClick={onEdgeClick}
      onPaneClick={onPaneClick}
      isValidConnection={isValidConnection}
      nodeTypes={nodeTypes}
      fitView
      style={{ background: 'transparent' }}
      defaultEdgeOptions={{
        type: 'default',
        animated: true,
      }}
    >
      <Background color="rgba(255,255,255,0.06)" gap={20} size={1} />
      <Controls />
      <MiniMap
        nodeColor={(n) => STANCE_COLORS[(n.data as any)?.role] || '#6b7280'}
        style={{ background: 'var(--bg-panel)' }}
      />
    </ReactFlow>
  );
}

export function WorkflowEditorCanvas() {
  return (
    <ReactFlowProvider>
      <FlowCanvas />
    </ReactFlowProvider>
  );
}
