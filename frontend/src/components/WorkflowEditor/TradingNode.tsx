// frontend/src/components/WorkflowEditor/TradingNode.tsx
// 交易执行节点 — React Flow 自定义节点，表示交易信号生成和执行

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

const TRADE_COLOR = '#FF6B35';

function TradingNodeComponent({ id, data, selected }: NodeProps) {
  const label = (data as any).label as string || '交易执行';

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${selected ? TRADE_COLOR : 'var(--border)'}`,
        borderRadius: 12,
        padding: '12px 16px',
        minWidth: 180,
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 14, color: TRADE_COLOR }}>💹</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 14 }}>{label}</span>
      </div>

      {/* 功能说明 */}
      <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.5 }}>
        信号生成 · 仓位管理 · 风控设置
      </div>

      {/* 右侧连接手柄（输出端） */}
      <Handle type="source" id="right" position={Position.Right}
        style={{ background: TRADE_COLOR, width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const TradingNode = memo(TradingNodeComponent);
