// frontend/src/components/WorkflowEditor/SkillNode.tsx
// 技能流程节点 — 表示一个独立的数据获取/分析技能，可连接到 Agent 节点

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

/** 技能类别 → 颜色映射 */
const CATEGORY_COLORS: Record<string, string> = {
  fundamental: '#34C759',
  technical: '#007AFF',
  sentiment: '#FF9500',
  news: '#AF52DE',
  macro: '#5AC8FA',
  data: '#8e8e93',
  sector: '#FF2D55',
  flow: '#FF3B30',
  analysis: '#64D2FF',
  general: '#8e8e93',
};

/** 技能节点图标（按类别） */
const CATEGORY_ICONS: Record<string, string> = {
  fundamental: '📊', technical: '📈', sentiment: '🔥',
  news: '📰', macro: '🌐', data: '💾',
  sector: '🔄', flow: '💧', analysis: '🔬', general: '⚙️',
};

function SkillNodeComponent({ data, selected }: NodeProps) {
  const d = data as any;
  const color = CATEGORY_COLORS[d.category] || '#8e8e93';

  return (
    <div
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
      }}
    >
      {/* 左侧输入：config 节点连接 */}
      <Handle type="target" id="left" position={Position.Left}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />

      {/* 标题行：类别图标 + 名称 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 12 }}>{CATEGORY_ICONS[d.category] || '⚙️'}</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 12, flex: 1 }}>{d.label}</span>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
      </div>

      {/* 技能标识（等宽字体） */}
      <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: 2 }}>
        {d.skillName}
      </div>

      {/* 右侧输出：analyst 节点连接 */}
      <Handle type="source" id="right" position={Position.Right}
        style={{ background: color, width: 12, height: 12, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const SkillNode = memo(SkillNodeComponent);
