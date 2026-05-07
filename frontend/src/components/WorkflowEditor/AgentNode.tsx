// frontend/src/components/WorkflowEditor/AgentNode.tsx
// Agent 画布节点组件 — React Flow 自定义节点，按角色着色，展示技能标签

import { memo, useState } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { useWorkflowStore } from '../../store/workflowStore';
import { AgentDetailModal } from './AgentDetailModal';
import { STANCE_COLORS } from '../../constants/theme';
import './pulse.css';

/**
 * AgentNodeComponent — React Flow 自定义分析师节点
 */
function AgentNodeComponent({ data, selected }: NodeProps) {
  const role = (data as any).role as string;
  const label = (data as any).label as string;
  const skills = (data as any).skills as string[];
  const color = STANCE_COLORS[role] || '#8e8e93';
  const analyzing = useWorkflowStore((s) => s.analyzingAgents.includes(role));
  const [showModal, setShowModal] = useState(false);

  return (
    <>
    <div
      className={analyzing ? 'agent-analyzing' : undefined}
      onClick={() => setShowModal(true)}
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${selected ? color : 'var(--border)'}`,
        borderRadius: 12,
        padding: '12px 16px',
        minWidth: 180,
        backdropFilter: 'var(--blur-light)',
        WebkitBackdropFilter: 'var(--blur-light)',
        boxShadow: analyzing
          ? `0 0 20px ${color}44, 0 4px 16px rgba(0,0,0,0.2)`
          : selected ? `0 0 16px ${color}33, 0 4px 16px rgba(0,0,0,0.15)` : 'var(--shadow-card)',
        transition: 'box-shadow 0.3s, border-color 0.2s',
      }}
    >
      {/* 顶部连接手柄（输入端） */}
      <Handle type="target" position={Position.Top} style={{ background: color, width: 10, height: 10, border: '2px solid var(--bg-card)' }} />

      {/* 角色名称行：颜色圆点 + 名称 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 14 }}>{label}</span>
      </div>

      {/* 技能标签列表（最多显示 3 个） */}
      <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
        {skills?.slice(0, 3).map((s: string) => (
          <span key={s} style={{
            display: 'inline-block', background: `${color}18`, color, borderRadius: 6,
            padding: '2px 8px', marginRight: 4, marginBottom: 2, fontSize: 10, fontWeight: 500,
          }}>{s}</span>
        ))}
        {skills && skills.length > 3 && <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>+{skills.length - 3}</span>}
      </div>

      {/* 底部连接手柄（输出端） */}
      <Handle type="source" position={Position.Bottom} style={{ background: color, width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
    </div>
    {showModal && <AgentDetailModal role={role} label={label} color={color} onClose={() => setShowModal(false)} />}
    </>
  );
}

export const AgentNode = memo(AgentNodeComponent);
