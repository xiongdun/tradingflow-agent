// frontend/src/components/Trading/TradeConfirmDialog.tsx
// 交易确认弹窗 — 显示订单详情，用户确认后提交

import { useCallback, useState } from 'react';

export interface PendingOrder {
  orderId: string;
  symbol: string;
  side: string;
  price: number;
  quantity: number;
  agentName?: string;
}

interface Props {
  order: PendingOrder;
  onConfirm: (orderId: string) => void;
  onCancel: (orderId: string) => void;
  onClose: () => void;
}

export function TradeConfirmDialog({ order, onConfirm, onCancel, onClose }: Props) {
  const [loading, setLoading] = useState<'confirm' | 'cancel' | null>(null);

  const handleConfirm = useCallback(async () => {
    setLoading('confirm');
    try {
      await onConfirm(order.orderId);
    } finally {
      setLoading(null);
    }
  }, [order.orderId, onConfirm]);

  const handleCancel = useCallback(async () => {
    setLoading('cancel');
    try {
      await onCancel(order.orderId);
    } finally {
      setLoading(null);
    }
  }, [order.orderId, onCancel]);

  const isBuy = order.side === 'buy';
  const totalAmount = order.price * order.quantity;

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: 'fixed', inset: 0, zIndex: 10001,
        background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'fadeIn 0.2s ease',
      }}
    >
      <div style={{
        background: 'var(--bg-panel)', borderRadius: 16, padding: '24px 28px',
        maxWidth: 420, width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        border: '1px solid var(--border)',
        animation: 'slideUp 0.25s ease',
      }}>
        {/* 标题 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <span style={{ fontSize: 24 }}>{isBuy ? '📈' : '📉'}</span>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)' }}>
              确认交易
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              {order.agentName ? `${order.agentName} 建议` : '手动交易'}
            </div>
          </div>
        </div>

        {/* 订单详情 */}
        <div style={{
          background: 'var(--bg-input)', borderRadius: 12, padding: '14px 16px',
          marginBottom: 16,
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 16px' }}>
            <DetailRow label="方向" value={
              <span style={{ color: isBuy ? 'var(--accent-red)' : 'var(--accent-green)', fontWeight: 700 }}>
                {isBuy ? '买入' : '卖出'}
              </span>
            } />
            <DetailRow label="代码" value={<span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{order.symbol}</span>} />
            <DetailRow label="价格" value={`¥${order.price.toFixed(2)}`} />
            <DetailRow label="数量" value={`${order.quantity} 股`} />
            <DetailRow label="金额" value={
              <span style={{ fontWeight: 700, color: 'var(--text)' }}>
                ¥{totalAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
              </span>
            } />
            <DetailRow label="订单号" value={<span style={{ fontFamily: 'monospace', fontSize: 11 }}>{order.orderId.slice(0, 8)}</span>} />
          </div>
        </div>

        {/* 安全提示 */}
        <div style={{
          background: 'rgba(255, 149, 0, 0.08)', borderRadius: 8, padding: '8px 12px',
          fontSize: 11, color: 'var(--accent-orange)', lineHeight: 1.5,
          marginBottom: 16,
        }}>
          ⚠️ 此操作将{isBuy ? '使用资金购买' : '卖出持有'} {order.symbol}，请确认交易信息无误。
        </div>

        {/* 操作按钮 */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button
            onClick={handleCancel}
            disabled={loading !== null}
            style={{
              background: 'var(--bg-input)', border: '1px solid var(--border)',
              borderRadius: 8, padding: '8px 20px', fontSize: 13, cursor: 'pointer',
              color: 'var(--text-secondary)',
              opacity: loading !== null ? 0.5 : 1,
            }}
          >
            {loading === 'cancel' ? '取消中...' : '取消'}
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading !== null}
            style={{
              background: isBuy ? 'var(--accent-red)' : 'var(--accent-green)',
              border: 'none', borderRadius: 8, padding: '8px 24px',
              fontSize: 13, fontWeight: 600, cursor: 'pointer', color: '#fff',
              boxShadow: `0 4px 12px ${isBuy ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)'}`,
              opacity: loading !== null ? 0.7 : 1,
            }}
          >
            {loading === 'confirm' ? '提交中...' : `确认${isBuy ? '买入' : '卖出'}`}
          </button>
        </div>
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 13, color: 'var(--text)' }}>{value}</div>
    </div>
  );
}
