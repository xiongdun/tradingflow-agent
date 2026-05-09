// frontend/src/components/WorkflowEditor/EventTriggerNode.tsx
// 事件触发器节点 — 监听市场事件并自动触发工作流

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { NODE_TYPE_COLORS, EVENT_ICONS } from '../../constants/theme';
import { useWorkflowStore } from '../../store/workflowStore';

function EventTriggerNodeComponent({ id, data, selected }: NodeProps) {
  const d = data as any;
  const color = NODE_TYPE_COLORS.event_trigger;
  const icon = EVENT_ICONS[d.eventType] || '⚡';
  const enabled = d.enabled !== false;
  const setSelectedNodeId = useWorkflowStore((s) => s.setSelectedNodeId);

  return (
    <div
      onClick={() => setSelectedNodeId(id)}
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${selected ? color : 'var(--border)'}`,
        borderRadius: 10,
        padding: '10px 14px',
        minWidth: 160,
        maxWidth: 220,
        opacity: enabled ? 1 : 0.5,
        backdropFilter: 'var(--blur-light)',
        WebkitBackdropFilter: 'var(--blur-light)',
        boxShadow: selected
          ? `0 0 16px ${color}33, 0 4px 16px rgba(0,0,0,0.15)`
          : 'var(--shadow-card)',
        transition: 'box-shadow 0.3s, border-color 0.2s, opacity 0.3s',
        cursor: 'pointer',
      }}
    >
      <Handle type="target" id="left" position={Position.Left}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 13 }}>{icon}</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 12, flex: 1 }}>
          {d.label || '事件触发'}
        </span>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: enabled ? color : 'var(--text-muted)',
          boxShadow: enabled ? `0 0 6px ${color}88` : 'none',
        }} />
      </div>

      <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 3 }}>
        {d.eventType || 'event'}{d.workflowName ? ` → ${d.workflowName}` : ''}
      </div>

      <Handle type="source" id="right" position={Position.Right}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const EventTriggerNode = memo(EventTriggerNodeComponent);
