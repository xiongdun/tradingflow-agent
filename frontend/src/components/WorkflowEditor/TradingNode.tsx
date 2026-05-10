// frontend/src/components/WorkflowEditor/TradingNode.tsx
// 交易员节点 — React Flow 自定义节点，三阶段投资组合经理：风险评估 → 风险管理 → 交易决策

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

const TRADE_COLOR = '#FF6B35';

/** 三阶段标签 */
const STAGES = [
  { label: '风险评估', icon: '🛡️' },
  { label: '风险管理', icon: '⚖️' },
  { label: '交易决策', icon: '💹' },
];

function TradingNodeComponent({ data, selected }: NodeProps) {
  const label = (data as any).label as string || '交易员';

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${selected ? TRADE_COLOR : 'var(--border)'}`,
        borderRadius: 12,
        padding: '12px 16px',
        minWidth: 200,
        backdropFilter: 'var(--blur-light)',
        WebkitBackdropFilter: 'var(--blur-light)',
        boxShadow: selected
          ? `0 0 16px ${TRADE_COLOR}33, 0 4px 16px rgba(0,0,0,0.15)`
          : 'var(--shadow-card)',
        transition: 'box-shadow 0.3s, border-color 0.2s',
      } as React.CSSProperties}
    >
      {/* 左侧连接手柄（输入端） */}
      <Handle type="target" id="left" position={Position.Left}
        style={{ background: TRADE_COLOR, width: 10, height: 10, border: '2px solid var(--bg-card)' }} />

      {/* 标题行：交易图标 + 名称 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 14, color: TRADE_COLOR }}>💹</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 13 }}>{label}</span>
      </div>

      {/* 三阶段流程指示 */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
        {STAGES.map((stage) => (
          <div key={stage.label} style={{
            flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
            background: 'rgba(255,107,53,0.06)', borderRadius: 6, padding: '3px 2px',
            border: '1px solid rgba(255,107,53,0.1)',
          }}>
            <span style={{ fontSize: 10 }}>{stage.icon}</span>
            <span style={{ fontSize: 8, color: 'var(--text-muted)', marginTop: 1, whiteSpace: 'nowrap' }}>
              {stage.label}
            </span>
          </div>
        ))}
      </div>

      {/* 流程箭头 */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2,
        fontSize: 8, color: 'var(--text-muted)', marginTop: 2,
      }}>
        <span>评估</span>
        <span style={{ color: TRADE_COLOR }}>→</span>
        <span>管理</span>
        <span style={{ color: TRADE_COLOR }}>→</span>
        <span>决策</span>
      </div>

      {/* 右侧连接手柄（输出端） */}
      <Handle type="source" id="right" position={Position.Right}
        style={{ background: TRADE_COLOR, width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const TradingNode = memo(TradingNodeComponent);
