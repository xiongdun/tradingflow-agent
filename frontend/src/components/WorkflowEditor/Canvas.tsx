// frontend/src/components/WorkflowEditor/Canvas.tsx
// 工作流画布 — React Flow 拖拽式画布，支持节点拖放、连线、缩放、小地图

import { useCallback } from 'react';
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

// 注册自定义节点类型（分析师节点 + 总结节点）
const nodeTypes = { analyst: AgentNode, summarizer: SummarizerNode };

/**
 * FlowCanvas — React Flow 画布核心组件
 * 功能：节点拖放、连线创建、点击选中、背景网格、缩放控件、小地图
 */
function FlowCanvas() {
  const {
    nodes, edges, setEdges, onNodesChange, onEdgesChange,
    addNode, setSelectedNodeId, agents,
  } = useWorkflowStore();
  const reactFlow = useReactFlow();

  /** 连线回调 — 用户从一个节点拖拽到另一个节点时创建边 */
  const onConnect = useCallback(
    (conn: Connection) => {
      if (conn.source && conn.target) {
        setEdges([...edges, {
          id: `${conn.source}-${conn.target}`,
          source: conn.source,
          target: conn.target,
        }]);
      }
    },
    [edges, setEdges],
  );

  /** 拖拽悬停回调 — 允许放置操作 */
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  /** 拖放回调 — 从侧边栏拖拽 Agent/总结节点到画布上创建新节点
   *  dataTransfer 格式：`type:role:label`（如 `analyst:fundamental:基本面分析师` 或 `summarizer:summarizer:总结研判`）
   */
  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const raw = e.dataTransfer.getData('application/reactflow');
      if (!raw) return;

      // 解析拖拽数据：兼容旧格式（纯 role）和新格式（type:role:label）
      const parts = raw.split(':');
      const nodeType = parts.length >= 3 ? parts[0] : 'analyst';
      const role = parts.length >= 3 ? parts[1] : raw;
      const label = parts.length >= 3 ? parts[2] : raw;

      // 同一 ID 不允许重复添加
      if (nodes.some((n) => n.id === role)) return;
      // 总结研判节点只允许一个
      if (nodeType === 'summarizer' && nodes.some((n) => n.type === 'summarizer')) return;

      // 将屏幕坐标转换为画布坐标
      const bounds = (e.target as HTMLElement).getBoundingClientRect();
      const position = reactFlow.screenToFlowPosition({
        x: e.clientX - bounds.left,
        y: e.clientY - bounds.top,
      });

      if (nodeType === 'summarizer') {
        addNode({
          id: 'summarizer',
          type: 'summarizer',
          position,
          data: { role: 'summarizer', label: '总结研判', skills: [] },
        });
      } else {
        const agent = agents.find((a) => a.role === role);
        addNode({
          id: role,
          type: 'analyst',
          position,
          data: { role, label: agent?.name || label || role, skills: agent?.current_skills || [] },
        });
      }
    },
    [reactFlow, nodes, agents, addNode],
  );

  /** 节点点击回调 — 选中节点以打开配置面板 */
  const onNodeClick = useCallback((_: any, node: any) => {
    setSelectedNodeId(node.id);
  }, [setSelectedNodeId]);

  /** 画布空白处点击回调 — 取消节点选中 */
  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, [setSelectedNodeId]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      nodeTypes={nodeTypes}
      fitView
      style={{ background: 'var(--bg)' }}
      defaultEdgeOptions={{ type: 'default', animated: true, style: { stroke: '#6366f1', strokeWidth: 2 } }}
    >
      {/* 背景网格 */}
      <Background color="var(--border)" gap={20} />
      {/* 缩放控件 */}
      <Controls />
      {/* 小地图 — 按角色着色 */}
      <MiniMap
        nodeColor={(n) => {
          return STANCE_COLORS[(n.data as any)?.role] || '#6b7280';
        }}
        style={{ background: 'var(--bg-panel)' }}
      />
    </ReactFlow>
  );
}

/**
 * WorkflowEditorCanvas — 工作流编辑器画布（带 Provider 包装）
 * ReactFlowProvider 提供画布上下文，FlowCanvas 是实际画布实现
 */
export function WorkflowEditorCanvas() {
  return (
    <ReactFlowProvider>
      <FlowCanvas />
    </ReactFlowProvider>
  );
}
