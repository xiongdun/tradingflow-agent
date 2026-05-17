// frontend/src/components/Trading/TradePanel.tsx
// 交易面板 — 账户概览、持仓列表、订单历史、券商连接

import { useState, useEffect, useCallback } from 'react';
import { showToast } from '../common/Toast';

interface AccountInfo {
  total_assets: number;
  available_cash: number;
  market_value: number;
  total_profit: number;
  today_profit: number;
}

interface PositionInfo {
  symbol: string;
  name: string;
  quantity: number;
  available_qty: number;
  cost_price: number;
  current_price: number;
  market_value: number;
  profit: number;
  profit_pct: number;
}

interface TradeOrder {
  id: string;
  symbol: string;
  market: string;
  side: string;
  price: number;
  quantity: number;
  status: string;
  created_at: string;
  note: string;
}

type TradeSubTab = 'account' | 'positions' | 'orders';

export function TradePanel() {
  const [subTab, setSubTab] = useState<TradeSubTab>('account');
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [positions, setPositions] = useState<PositionInfo[]>([]);
  const [orders, setOrders] = useState<TradeOrder[]>([]);
  const [tradingStatus, setTradingStatus] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, accRes, posRes, ordRes] = await Promise.allSettled([
        fetch('/api/trading/status').then((r) => r.json()),
        fetch('/api/trading/account').then((r) => r.json()),
        fetch('/api/trading/positions').then((r) => r.json()),
        fetch('/api/trading/orders').then((r) => r.json()),
      ]);
      if (statusRes.status === 'fulfilled') setTradingStatus(statusRes.value);
      if (accRes.status === 'fulfilled') setAccount(accRes.value);
      if (posRes.status === 'fulfilled') setPositions(posRes.value);
      if (ordRes.status === 'fulfilled') setOrders(ordRes.value);
    } catch {
      showToast('获取交易数据失败', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleConfirmOrder = useCallback(async (orderId: string) => {
    try {
      const res = await fetch(`/api/trading/orders/${orderId}/confirm`, { method: 'POST' });
      if (res.ok) {
        showToast('订单已确认', 'success');
        fetchAll();
      } else {
        showToast('确认失败', 'error');
      }
    } catch {
      showToast('网络错误', 'error');
    }
  }, [fetchAll]);

  const handleCancelOrder = useCallback(async (orderId: string) => {
    try {
      const res = await fetch(`/api/trading/orders/${orderId}/cancel`, { method: 'POST' });
      if (res.ok) {
        showToast('订单已取消', 'success');
        fetchAll();
      }
    } catch {
      showToast('网络错误', 'error');
    }
  }, [fetchAll]);

  const mode = (tradingStatus.mode as string) || 'simulated';
  const connected = tradingStatus.connected as boolean;
  const pendingCount = (tradingStatus.pending_orders as number) || 0;

  return (
    <div style={{ padding: '16px 24px', height: '100%', overflow: 'auto' }}>
      {/* 交易系统状态栏 */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20,
        padding: '10px 16px', borderRadius: 10,
        background: mode === 'simulated' ? 'rgba(99,102,241,0.08)' : 'rgba(34,197,94,0.08)',
        border: `1px solid ${mode === 'simulated' ? 'rgba(99,102,241,0.2)' : 'rgba(34,197,94,0.2)'}`,
      }}>
        <span style={{ fontSize: 18 }}>{mode === 'simulated' ? '🧪' : '🏦'}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>
            {mode === 'simulated' ? '模拟交易' : '实盘交易'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {mode === 'simulated' ? '所有订单均为模拟执行' : connected ? '已连接券商' : '未连接'}
          </div>
        </div>
        {pendingCount > 0 && (
          <span style={{
            background: 'var(--accent-orange)', color: '#fff', borderRadius: 10,
            padding: '2px 8px', fontSize: 11, fontWeight: 600,
          }}>
            {pendingCount} 待确认
          </span>
        )}
        <button
          onClick={fetchAll}
          disabled={loading}
          style={{
            background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer',
            color: 'var(--text-secondary)',
          }}
        >
          {loading ? '刷新中...' : '🔄 刷新'}
        </button>
      </div>

      {/* 子标签页 */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
        {([
          { key: 'account', label: '💰 账户' },
          { key: 'positions', label: '📦 持仓' },
          { key: 'orders', label: '📋 订单' },
        ] as { key: TradeSubTab; label: string }[]).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSubTab(tab.key)}
            style={{
              padding: '6px 16px', fontSize: 12, fontWeight: subTab === tab.key ? 600 : 400,
              background: subTab === tab.key ? 'var(--bg-elevated)' : 'transparent',
              color: subTab === tab.key ? 'var(--text)' : 'var(--text-muted)',
              border: 'none', borderRadius: 6, cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 内容 */}
      {subTab === 'account' && <AccountView account={account} />}
      {subTab === 'positions' && <PositionsView positions={positions} />}
      {subTab === 'orders' && (
        <OrdersView
          orders={orders}
          onConfirm={handleConfirmOrder}
          onCancel={handleCancelOrder}
        />
      )}
    </div>
  );
}

function AccountView({ account }: { account: AccountInfo | null }) {
  if (!account) {
    return <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 40 }}>加载中...</div>;
  }

  const profitColor = account.total_profit >= 0 ? 'var(--accent-red)' : 'var(--accent-green)';

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
      <StatCard label="总资产" value={`¥${account.total_assets.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`} />
      <StatCard label="可用资金" value={`¥${account.available_cash.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`} />
      <StatCard label="持仓市值" value={`¥${account.market_value.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`} />
      <StatCard
        label="总盈亏"
        value={`${account.total_profit >= 0 ? '+' : ''}¥${account.total_profit.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`}
        color={profitColor}
      />
    </div>
  );
}

function PositionsView({ positions }: { positions: PositionInfo[] }) {
  if (positions.length === 0) {
    return <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 40 }}>暂无持仓</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {positions.map((p) => (
        <div key={p.symbol} style={{
          display: 'flex', alignItems: 'center', gap: 16, padding: '10px 14px',
          background: 'var(--bg-input)', borderRadius: 8,
        }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
              {p.name || p.symbol}
              <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>
                {p.symbol}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              {p.quantity}股 · 成本 ¥{p.cost_price.toFixed(2)} · 现价 ¥{p.current_price.toFixed(2)}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{
              fontSize: 13, fontWeight: 600,
              color: p.profit >= 0 ? 'var(--accent-red)' : 'var(--accent-green)',
            }}>
              {p.profit >= 0 ? '+' : ''}¥{p.profit.toFixed(2)}
            </div>
            <div style={{
              fontSize: 11,
              color: p.profit_pct >= 0 ? 'var(--accent-red)' : 'var(--accent-green)',
            }}>
              {p.profit_pct >= 0 ? '+' : ''}{p.profit_pct.toFixed(2)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function OrdersView({ orders, onConfirm, onCancel }: {
  orders: TradeOrder[];
  onConfirm: (id: string) => void;
  onCancel: (id: string) => void;
}) {
  if (orders.length === 0) {
    return <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 40 }}>暂无订单</div>;
  }

  const statusColors: Record<string, string> = {
    pending: 'var(--accent-orange)',
    confirmed: 'var(--accent-blue)',
    submitted: 'var(--accent-blue)',
    filled: 'var(--accent-green)',
    rejected: 'var(--accent-red)',
    cancelled: 'var(--text-muted)',
  };

  const statusLabels: Record<string, string> = {
    pending: '待确认',
    confirmed: '已确认',
    submitted: '已提交',
    filled: '已成交',
    rejected: '已拒绝',
    cancelled: '已取消',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {orders.map((o) => (
        <div key={o.id} style={{
          display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
          background: 'var(--bg-input)', borderRadius: 8,
        }}>
          <div style={{ fontSize: 16 }}>{o.side === 'buy' ? '📈' : '📉'}</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
              {o.side === 'buy' ? '买入' : '卖出'} {o.symbol}
              <span style={{
                marginLeft: 8, fontSize: 11, fontWeight: 600,
                color: statusColors[o.status] || 'var(--text-muted)',
              }}>
                {statusLabels[o.status] || o.status}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              {o.quantity}股 · ¥{o.price.toFixed(2)} · {new Date(o.created_at).toLocaleTimeString('zh-CN')}
            </div>
          </div>
          {o.status === 'pending' && (
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                onClick={() => onConfirm(o.id)}
                style={{
                  background: 'var(--accent-blue)', color: '#fff', border: 'none',
                  borderRadius: 6, padding: '4px 12px', fontSize: 11, cursor: 'pointer',
                }}
              >
                确认
              </button>
              <button
                onClick={() => onCancel(o.id)}
                style={{
                  background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                  borderRadius: 6, padding: '4px 12px', fontSize: 11, cursor: 'pointer',
                  color: 'var(--text-muted)',
                }}
              >
                取消
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{
      padding: '12px 16px', background: 'var(--bg-input)', borderRadius: 10,
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || 'var(--text)', fontFamily: 'monospace' }}>
        {value}
      </div>
    </div>
  );
}
