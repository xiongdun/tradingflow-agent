// frontend/src/components/WorkflowEditor/AgentNode.tsx
// Agent 画布节点组件 — React Flow 自定义节点，按角色着色，展示技能标签

import { memo, useEffect, useRef } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { useWorkflowStore } from '../../store/workflowStore';
import { STANCE_COLORS } from '../../constants/theme';
import './pulse.css';

/**
 * AgentNodeComponent — React Flow 自定义分析师节点
 * 点击仅选中节点，分析详情在右侧 NodeConfig 面板展示
 */

/** Agent 角色 → 图标映射 */
const ROLE_ICONS: Record<string, string> = {
  fundamental: '📊', technical: '📈', sentiment: '🔥',
  news: '📰', macro: '🌐', hot_money: '💰',
  risk: '⚠️', summarizer: '✦',
};

/** 将 hex 颜色转为 RGB 分量，用于 CSS 自定义属性 */
function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '');
  return [
    parseInt(h.substring(0, 2), 16),
    parseInt(h.substring(2, 4), 16),
    parseInt(h.substring(4, 6), 16),
  ];
}

function AgentNodeComponent({ id, data, selected }: NodeProps) {
  const role = (data as any).role as string;
  const label = (data as any).label as string;
  const skills = (data as any).skills as string[];
  const color = STANCE_COLORS[role] || '#8e8e93';
  const analyzing = useWorkflowStore((s) => s.analyzingAgents.includes(role));
  const setSelectedNodeId = useWorkflowStore((s) => s.setSelectedNodeId);
  const [r, g, b] = hexToRgb(color);
  const selfRef = useRef<HTMLDivElement>(null);

  // 将 --pulse-r/g/b 设在外层 .react-flow__node wrapper 上，
  // 以便 pulse.css 中 wrapper-pulse 动画能读取这些变量
  useEffect(() => {
    const el = selfRef.current;
    if (!el) return;
    // 向上找到 React Flow 生成的 wrapper 节点（data-id="xxx"）
    const wrapper = el.closest<HTMLElement>('.react-flow__node');
    if (wrapper) {
      wrapper.style.setProperty('--pulse-r', String(r));
      wrapper.style.setProperty('--pulse-g', String(g));
      wrapper.style.setProperty('--pulse-b', String(b));
    }
  }, [r, g, b]);

  return (
    <div
      ref={selfRef}
      className={analyzing ? 'agent-analyzing' : undefined}
      onClick={() => setSelectedNodeId(id)}
      style={{
        '--pulse-r': r,
        '--pulse-g': g,
        '--pulse-b': b,
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
        cursor: 'pointer',
      } as React.CSSProperties}
    >
      {/* 左侧连接手柄（输入端） */}
      <Handle type="target" id="left" position={Position.Left} style={{ background: color, width: 10, height: 10, border: '2px solid var(--bg-card)' }} />

      {/* 角色名称行：类型图标 + 名称 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 14, color }}>{ROLE_ICONS[role] || '🧠'}</span>
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

      {/* 右侧连接手柄（输出端） */}
      <Handle type="source" id="right" position={Position.Right} style={{ background: color, width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const AgentNode = memo(AgentNodeComponent);
