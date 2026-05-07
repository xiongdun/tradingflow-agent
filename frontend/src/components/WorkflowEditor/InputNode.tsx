// frontend/src/components/WorkflowEditor/InputNode.tsx
// 输入流程节点 — 股票代码 + 市场选择，可编辑的输入节点

import { memo, useCallback } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { useWorkflowStore } from '../../store/workflowStore';

function InputNodeComponent({ id, data, selected }: NodeProps) {
  const d = data as any;
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData);
  const setSelectedSymbol = useWorkflowStore((s) => s.setSelectedSymbol);
  const setSelectedMarket = useWorkflowStore((s) => s.setSelectedMarket);

  const onSymbolChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    updateNodeData(id, { symbol: val });
    setSelectedSymbol(val);
  }, [id, updateNodeData, setSelectedSymbol]);

  const onMarketChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    updateNodeData(id, { market: val });
    setSelectedMarket(val);
  }, [id, updateNodeData, setSelectedMarket]);

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${selected ? 'var(--accent-green)' : 'var(--border)'}`,
        borderRadius: 12,
        padding: '12px 16px',
        minWidth: 180,
        backdropFilter: 'var(--blur-light)',
        WebkitBackdropFilter: 'var(--blur-light)',
        boxShadow: selected
          ? '0 0 16px rgba(52,199,89,0.25), 0 4px 16px rgba(0,0,0,0.15)'
          : 'var(--shadow-card)',
        transition: 'box-shadow 0.3s, border-color 0.2s',
      }}
    >
      {/* 标题行 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 14, color: 'var(--accent-green)' }}>◆</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 13 }}>输入</span>
      </div>

      {/* 股票代码 — 可编辑输入框 */}
      <div style={{ marginBottom: 8 }}>
        <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 3 }}>股票代码</label>
        <input
          type="text"
          value={d.symbol || ''}
          onChange={onSymbolChange}
          placeholder="如 600519"
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '6px 10px', color: 'var(--accent-green)',
            fontSize: 14, fontWeight: 700, fontFamily: 'monospace', outline: 'none',
          }}
        />
      </div>

      {/* 市场 — 可编辑下拉 */}
      <div>
        <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 3 }}>市场</label>
        <select
          value={d.market || 'a_share'}
          onChange={onMarketChange}
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '6px 10px', color: 'var(--text-secondary)',
            fontSize: 13, fontWeight: 600, outline: 'none', cursor: 'pointer',
          }}
        >
          <option value="a_share">A股</option>
          <option value="h_stock">港股</option>
          <option value="us_stock">美股</option>
        </select>
      </div>

      {/* 右侧输出 */}
      <Handle type="source" id="right" position={Position.Right}
        style={{ background: 'var(--accent-green)', width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const InputNode = memo(InputNodeComponent);
