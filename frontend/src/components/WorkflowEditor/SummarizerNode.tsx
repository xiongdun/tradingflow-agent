// frontend/src/components/WorkflowEditor/SummarizerNode.tsx
// 总结研判节点 — React Flow 自定义节点，汇总所有分析师意见生成最终报告

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

/**
 * SummarizerNodeComponent — 总结研判节点
 */
function SummarizerNodeComponent({ data, selected }: NodeProps) {
  const label = (data as any).label || '总结研判';
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: `1px solid ${selected ? 'var(--accent-purple)' : 'var(--border)'}`,
      borderRadius: 14, padding: '16px 24px', minWidth: 200, textAlign: 'center',
      backdropFilter: 'var(--blur-light)',
      WebkitBackdropFilter: 'var(--blur-light)',
      boxShadow: selected
        ? '0 0 20px rgba(175, 82, 222, 0.2), 0 4px 16px rgba(0,0,0,0.15)'
        : 'var(--shadow-card)',
      transition: 'box-shadow 0.3s, border-color 0.2s',
    }}>
      {/* 顶部连接手柄（接收分析师输出） */}
      <Handle type="target" position={Position.Top} style={{ background: 'var(--accent-purple)', width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
      {/* 图标 */}
      <div style={{ fontSize: 22, marginBottom: 4 }}>✦</div>
      {/* 节点标签 */}
      <div style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15 }}>{label}</div>
      {/* 功能描述 */}
      <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>综合所有观点 → 最终研判</div>
      {/* 底部连接手柄（输出最终报告） */}
      <Handle type="source" position={Position.Bottom} style={{ background: 'var(--accent-purple)', width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const SummarizerNode = memo(SummarizerNodeComponent);
