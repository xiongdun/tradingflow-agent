// frontend/src/components/WorkflowEditor/ConditionNode.tsx
// 条件分支节点 — 根据状态字段路由到不同下游节点

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { NODE_TYPE_COLORS } from '../../constants/theme';

function ConditionNodeComponent({ data, selected }: NodeProps) {
  const d = data as any;
  const color = NODE_TYPE_COLORS.condition;
  const rules = d.rules || [];

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: `1px solid ${selected ? color : 'var(--border)'}`,
      borderRadius: 10,
      padding: '10px 14px',
      minWidth: 160,
      maxWidth: 220,
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
        <span style={{ fontSize: 13, color, fontWeight: 700 }}>◇</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 12, flex: 1 }}>
          {d.label || '条件分支'}
        </span>
      </div>

      <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 3 }}>
        field: {d.field || 'opinions'}
      </div>

      {rules.length > 0 && (
        <div style={{ marginTop: 4 }}>
          {rules.map((rule: any, i: number) => (
            <div key={i} style={{
              fontSize: 9, color: 'var(--text-secondary)',
              background: `${color}10`, borderRadius: 4,
              padding: '2px 6px', marginBottom: 2,
            }}>
              {rule.label}{rule.description ? `: ${rule.description}` : ''}
            </div>
          ))}
        </div>
      )}

      <Handle type="source" id="right" position={Position.Right}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const ConditionNode = memo(ConditionNodeComponent);
