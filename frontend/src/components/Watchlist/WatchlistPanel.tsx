// frontend/src/components/Watchlist/WatchlistPanel.tsx
// 自选股面板 — 添加/删除关注股票，支持批量一键分析

import { useState, useEffect, useCallback } from 'react';
import { t } from '../../i18n';

interface WatchItem {
  id: number;
  symbol: string;
  market: string;
  name: string;
  group_name: string;
  added_at: string;
}

function getMarketLabel(m: string) { return t(`market.${m}`) || m; }

export function WatchlistPanel() {
  const [items, setItems] = useState<WatchItem[]>([]);
  const [symbol, setSymbol] = useState('');
  const [market, setMarket] = useState('a_share');
  const [name, setName] = useState('');
  const [group, setGroup] = useState('');
  const [loading, setLoading] = useState(false);
  const [batchRunning, setBatchRunning] = useState(false);

  const load = useCallback(async () => {
    try {
      const resp = await fetch('/api/watchlist');
      const data = await resp.json();
      setItems(data.items || []);
    } catch { setItems([]); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = async () => {
    if (!symbol.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: symbol.trim(), market, name: name.trim() || symbol.trim(), group_name: group.trim() }),
      });
      if (resp.ok) { setSymbol(''); setName(''); load(); }
    } catch {}
    setLoading(false);
  };

  const remove = async (id: number) => {
    await fetch(`/api/watchlist/${id}`, { method: 'DELETE' });
    load();
  };

  const batchAnalyze = async () => {
    if (items.length === 0) return;
    setBatchRunning(true);
    try {
      await fetch('/api/watchlist/batch-analyze', { method: 'POST' });
    } catch {}
    setBatchRunning(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg)' }}>
      {/* 顶部操作栏 */}
      <div style={{ display: 'flex', gap: 8, padding: '8px 16px', borderBottom: '1px solid var(--border)', background: 'var(--bg-panel)', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder={t("watchlist.placeholder_symbol")}
          style={inputStyle}
        />
        <select value={market} onChange={(e) => setMarket(e.target.value)} style={inputStyle}>
          <option value="a_share">{t("market.a_share")}</option>
          <option value="h_stock">{t("market.h_stock")}</option>
          <option value="us_stock">{t("market.us_stock")}</option>
        </select>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder={t("watchlist.placeholder_name")} style={inputStyle} />
        <input value={group} onChange={(e) => setGroup(e.target.value)} placeholder={t("watchlist.placeholder_group")} style={{ ...inputStyle, width: 100 }} />
        <button onClick={add} disabled={loading} style={primaryBtn}>
          {loading ? t("common.adding") : t("watchlist.add")}
        </button>
        <div style={{ flex: 1 }} />
        <button onClick={batchAnalyze} disabled={batchRunning || items.length === 0} style={{ ...primaryBtn, background: '#10b981' }}>
          {batchRunning ? t("watchlist.batch_running") : t("watchlist.batch")}
        </button>
      </div>

      {/* 列表 */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {items.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', paddingTop: 40 }}>
            {t("watchlist.empty")}
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("watchlist.symbol")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("watchlist.name_label")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.market")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("watchlist.group")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("watchlist.added_at")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.action")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '6px 8px', fontWeight: 600 }}>{it.symbol}</td>
                  <td style={{ padding: '6px 8px' }}>{it.name}</td>
                  <td style={{ padding: '6px 8px' }}>{getMarketLabel(it.market)}</td>
                  <td style={{ padding: '6px 8px', color: 'var(--text-muted)' }}>{it.group_name || '-'}</td>
                  <td style={{ padding: '6px 8px', color: 'var(--text-secondary)' }}>
                    {new Date(it.added_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <button onClick={() => remove(it.id)} style={{ ...primaryBtn, background: '#ef4444' }}>{t("common.delete")}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: 'var(--bg-input)', border: '1px solid var(--border-strong)', borderRadius: 4,
  padding: '4px 8px', color: 'var(--text)', fontSize: 12, width: 110,
};

const primaryBtn: React.CSSProperties = {
  background: '#6366f1', color: '#fff', border: 'none', borderRadius: 4,
  padding: '4px 14px', fontSize: 12, cursor: 'pointer', fontWeight: 600,
};
