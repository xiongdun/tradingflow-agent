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
 * 展示角色名称、颜色标识、技能标签（最多显示 3 个，超出显示 +N）
 * 上下各有一个连接手柄（Handle），用于与其他节点连线
 */
function AgentNodeComponent({ data, selected }: NodeProps) {
  const role = (data as any).role as string;
  const label = (data as any).label as string;
  const skills = (data as any).skills as string[];
  const color = STANCE_COLORS[role] || '#6b7280';  // 未知角色用灰色
  const analyzing = useWorkflowStore((s) => s.analyzingAgents.includes(role));
  const [showModal, setShowModal] = useState(false);

  return (
    <>
    <div
      className={analyzing ? 'agent-analyzing' : undefined}
      onClick={() => setShowModal(true)}
      style={{
        background: 'var(--bg-card)',
        border: `2px solid ${selected ? 'var(--text)' : color}`,
        borderRadius: 12,
        padding: '12px 16px',
        minWidth: 180,
        boxShadow: analyzing
          ? `0 0 12px ${color}aa, 0 0 24px ${color}44`
          : selected ? `0 0 16px ${color}88` : '0 2px 8px rgba(0,0,0,0.3)',
      }}
    >
      {/* 顶部连接手柄（输入端） */}
      <Handle type="target" position={Position.Top} style={{ background: color }} />

      {/* 角色名称行：颜色圆点 + 名称 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 14 }}>{label}</span>
      </div>

      {/* 技能标签列表（最多显示 3 个） */}
      <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
        {skills?.slice(0, 3).map((s: string) => (
          <span key={s} style={{
            display: 'inline-block', background: `${color}22`, color, borderRadius: 4,
            padding: '1px 6px', marginRight: 4, marginBottom: 2, fontSize: 10,
          }}>{s}</span>
        ))}
        {skills && skills.length > 3 && <span style={{ color: 'var(--text-muted)' }}>+{skills.length - 3}</span>}
      </div>

      {/* 底部连接手柄（输出端） */}
      <Handle type="source" position={Position.Bottom} style={{ background: color }} />
    </div>
    {showModal && <AgentDetailModal role={role} label={label} color={color} onClose={() => setShowModal(false)} />}
    </>
  );
}

// 使用 memo 避免无关状态变化导致的重渲染
export const AgentNode = memo(AgentNodeComponent);
