// frontend/src/components/WorkflowEditor/SummarizerNode.tsx
// 总结研判节点 — React Flow 自定义节点，汇总所有分析师意见生成最终报告

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

/**
 * SummarizerNodeComponent — 总结研判节点
 * 作为工作流的终端节点，接收所有分析师节点的输出
 * 使用紫色渐变背景和金色选中效果，与分析师节点区分
 */
function SummarizerNodeComponent({ data, selected }: NodeProps) {
  const label = (data as any).label || '总结研判';
  return (
    <div style={{
      background: 'linear-gradient(135deg, var(--bg-card), #2a2a3e)',  // 紫色渐变背景
      border: `2px solid ${selected ? '#fbbf24' : '#a78bfa'}`,  // 选中时金色，否则紫色
      borderRadius: 16, padding: '16px 24px', minWidth: 200, textAlign: 'center',
      boxShadow: selected ? '0 0 20px #a78bfa88' : '0 4px 12px rgba(0,0,0,0.4)',
    }}>
      {/* 顶部连接手柄（接收分析师输出） */}
      <Handle type="target" position={Position.Top} style={{ background: '#a78bfa' }} />
      {/* 机器人图标 */}
      <div style={{ fontSize: 20, marginBottom: 4 }}>🤖</div>
      {/* 节点标签 */}
      <div style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15 }}>{label}</div>
      {/* 功能描述 */}
      <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>综合所有观点 → 最终研判</div>
      {/* 底部连接手柄（输出最终报告） */}
      <Handle type="source" position={Position.Bottom} style={{ background: '#a78bfa' }} />
    </div>
  );
}

// 使用 memo 避免无关状态变化导致的重渲染
export const SummarizerNode = memo(SummarizerNodeComponent);
