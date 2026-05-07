// frontend/src/components/WorkflowEditor/ConfigNode.tsx
// 配置流程节点 — 分析参数（K线周期、历史天数），可编辑，连接到技能节点传参

import { memo, useCallback } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { useWorkflowStore } from '../../store/workflowStore';

function ConfigNodeComponent({ id, data, selected }: NodeProps) {
  const d = data as any;
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData);

  const onPeriodChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    updateNodeData(id, { period: e.target.value });
  }, [id, updateNodeData]);

  const onDaysChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    updateNodeData(id, { days: parseInt(e.target.value) || 120 });
  }, [id, updateNodeData]);

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${selected ? 'var(--accent-orange)' : 'var(--border)'}`,
        borderRadius: 12,
        padding: '12px 16px',
        minWidth: 170,
        backdropFilter: 'var(--blur-light)',
        WebkitBackdropFilter: 'var(--blur-light)',
        boxShadow: selected
          ? '0 0 16px rgba(255,149,0,0.25), 0 4px 16px rgba(0,0,0,0.15)'
          : 'var(--shadow-card)',
        transition: 'box-shadow 0.3s, border-color 0.2s',
      }}
    >
      {/* 标题行 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 14, color: 'var(--accent-orange)' }}>⚙</span>
        <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 13 }}>参数配置</span>
      </div>

      {/* K线周期 — 下拉选择 */}
      <div style={{ marginBottom: 8 }}>
        <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 3 }}>K线周期</label>
        <select
          value={d.period || 'daily'}
          onChange={onPeriodChange}
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '6px 10px', color: 'var(--text-secondary)',
            fontSize: 13, fontWeight: 600, outline: 'none', cursor: 'pointer',
          }}
        >
          <option value="daily">日K</option>
          <option value="weekly">周K</option>
          <option value="monthly">月K</option>
        </select>
      </div>

      {/* 历史天数 — 数字输入 */}
      <div>
        <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 3 }}>历史天数</label>
        <input
          type="number"
          value={d.days || 120}
          onChange={onDaysChange}
          min={10}
          max={365}
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '6px 10px', color: 'var(--text-secondary)',
            fontSize: 13, fontWeight: 600, outline: 'none',
          }}
        />
      </div>

      {/* 右侧输出：连接到 skill 节点 */}
      <Handle type="source" id="right" position={Position.Right}
        style={{ background: 'var(--accent-orange)', width: 10, height: 10, border: '2px solid var(--bg-card)' }} />
    </div>
  );
}

export const ConfigNode = memo(ConfigNodeComponent);
