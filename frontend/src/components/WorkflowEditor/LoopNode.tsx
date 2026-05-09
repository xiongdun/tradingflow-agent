// frontend/src/components/WorkflowEditor/LoopNode.tsx
// 循环节点 — 控制工作流中重复执行的逻辑

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { NODE_TYPE_COLORS } from '../../constants/theme';

function LoopNodeComponent({ data, selected }: NodeProps) {
  const d = data as any;
  const color = NODE_TYPE_COLORS.loop;
  const maxIter = d.maxIterations || 3;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: `1px solid ${selected ? color : 'var(--border)'}`,
      borderRadius: 10,
      padding: '10px 14px',
      minWidth: 140,
      maxWidth: 200,
      backdropFilter: 'var(--blur-light)',
      WebkitBackdropFilter: 'var(--blur-light)',
      boxShadow: selected
        ? `0 0 16px ${color}33, 0 4px 16px rgba(0,0,0,0.15)`
        : 'var(--shadow-card)',
      transition: 'box-shadow 0.3s, border-color 0.2s',
    }}>
      <Handle type="target" id="left" position={Position.Left}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 14, color, fontWeight: 700 }}>↻</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 12 }}>
          {d.label || '循环'}
        </span>
      </div>

      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
        最大迭代: <span style={{ color, fontWeight: 600 }}>{maxIter}</span>
      </div>

      <Handle type="source" id="right" position={Position.Right}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const LoopNode = memo(LoopNodeComponent);
