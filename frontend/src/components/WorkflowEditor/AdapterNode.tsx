// frontend/src/components/WorkflowEditor/AdapterNode.tsx
// 适配器流程节点 — 包装外部项目（HTTP/Docker/MCP等）为工作流节点

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { NODE_TYPE_COLORS, ADAPTER_ICONS } from '../../constants/theme';
import { useWorkflowStore } from '../../store/workflowStore';

function AdapterNodeComponent({ id, data, selected }: NodeProps) {
  const d = data as any;
  const color = NODE_TYPE_COLORS.adapter;
  const icon = ADAPTER_ICONS[d.adapterType] || '🧩';
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
        backdropFilter: 'var(--blur-light)',
        WebkitBackdropFilter: 'var(--blur-light)',
        boxShadow: selected
          ? `0 0 16px ${color}33, 0 4px 16px rgba(0,0,0,0.15)`
          : 'var(--shadow-card)',
        transition: 'box-shadow 0.3s, border-color 0.2s',
        cursor: 'pointer',
      }}
    >
      <Handle type="target" id="left" position={Position.Left}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 13 }}>{icon}</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 12, flex: 1 }}>
          {d.label || d.adapterName || '适配器'}
        </span>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
      </div>

      <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 3 }}>
        {d.adapterType}{d.outputKey ? ` → ${d.outputKey}` : ''}
      </div>

      <Handle type="source" id="right" position={Position.Right}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const AdapterNode = memo(AdapterNodeComponent);
