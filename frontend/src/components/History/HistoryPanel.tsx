// frontend/src/components/History/HistoryPanel.tsx
// 历史记录面板 — 查询分析历史、查看详情、回测统计

import { useState, useEffect, useCallback } from 'react';
import Markdown from 'react-markdown';
import { t } from '../../i18n';

interface HistoryRecord {
  id: number;
  symbol: string;
  market: string;
  workflow: string;
  agents: string[];
  opinions_count: number;
  created_at: string;
}

interface HistoryDetail {
  id: number;
  symbol: string;
  market: string;
  workflow: string;
  agents: string[];
  opinions: any[];
  report: any;
  markdown: string;
  created_at: string;
}

interface BacktestResult {
  symbol: string;
  days: number;
  records: number;
  total_predictions: number;
  agent_stats: Record<string, { name: string; total: number; stances: Record<string, number> }>;
}

const MARKET_LABELS: Record<string, string> = { a_share: '', h_stock: '', us_stock: '' };
function getMarketLabel(m: string) { return t(`market.${m}`) || m; }

export function HistoryPanel() {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [selected, setSelected] = useState<HistoryDetail | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [filterSymbol, setFilterSymbol] = useState('');
  const [filterMarket, setFilterMarket] = useState('');
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'list' | 'detail' | 'backtest'>('list');

  /** 加载历史记录列表 */
  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterSymbol) params.set('symbol', filterSymbol);
      if (filterMarket) params.set('market', filterMarket);
      const resp = await fetch(`/api/history?${params}`);
      const data = await resp.json();
      setRecords(data.records || []);
    } catch {
      setRecords([]);
    }
    setLoading(false);
  }, [filterSymbol, filterMarket]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  /** 查看详情 */
  const viewDetail = async (id: number) => {
    try {
      const resp = await fetch(`/api/history/${id}`);
      const data = await resp.json();
      if (!data.error) {
        setSelected(data);
        setTab('detail');
      }
    } catch {}
  };

  /** 删除记录 */
  const deleteRecord = async (id: number) => {
    await fetch(`/api/history/${id}`, { method: 'DELETE' });
    loadHistory();
  };

  /** 运行回测 */
  const runBacktest = async (symbol: string) => {
    try {
      const resp = await fetch(`/api/backtest?symbol=${symbol}&days=30`);
      const data = await resp.json();
      setBacktestResult(data);
      setTab('backtest');
    } catch {}
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg)' }}>
      {/* 子标签页 */}
      <div style={{ display: 'flex', gap: 8, padding: '8px 16px', borderBottom: '1px solid var(--border)', background: 'var(--bg-panel)' }}>
        {(['list', 'detail', 'backtest'] as const).map((tabKey2) => (
          <button
            key={tabKey2}
            onClick={() => setTab(tabKey2)}
            disabled={tabKey2 !== 'list' && !selected && !backtestResult}
            style={{
              padding: '4px 16px', fontSize: 12, fontWeight: 600,
              background: tab === tabKey2 ? 'var(--bg-input)' : 'transparent',
              color: tab === tabKey2 ? 'var(--text)' : 'var(--text-muted)',
              border: 'none', borderBottom: tab === tabKey2 ? '2px solid #6366f1' : '2px solid transparent',
              cursor: 'pointer', opacity: tabKey2 !== 'list' && !selected && !backtestResult ? 0.4 : 1,
            }}
          >
            {t(tabKey2 === "list" ? "history.title" : tabKey2 === "detail" ? "history.detail" : "history.backtest")}
          </button>
        ))}

        {/* 过滤器 */}
        <div style={{ flex: 1 }} />
        <input
          value={filterSymbol}
          onChange={(e) => setFilterSymbol(e.target.value)}
          placeholder={t("watchlist.placeholder_symbol")}
          style={{
            background: 'var(--bg-input)', border: '1px solid var(--border-strong)', borderRadius: 4,
            padding: '3px 8px', color: 'var(--text)', fontSize: 12, width: 100,
          }}
        />
        <select
          value={filterMarket}
          onChange={(e) => setFilterMarket(e.target.value)}
          style={{
            background: 'var(--bg-input)', border: '1px solid var(--border-strong)', borderRadius: 4,
            padding: '3px 8px', color: 'var(--text)', fontSize: 12,
          }}
        >
          <option value="">{t("common.all_markets")}</option>
          <option value="a_share">{t("market.a_share")}</option>
          <option value="h_stock">{t("market.h_stock")}</option>
          <option value="us_stock">{t("market.us_stock")}</option>
        </select>
        <button
          onClick={loadHistory}
          style={{
            background: '#6366f1', color: '#fff', border: 'none', borderRadius: 4,
            padding: '3px 12px', fontSize: 12, cursor: 'pointer',
          }}
        >
          {t("common.search")}
        </button>
      </div>

      {/* 内容区域 */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {tab === 'list' && (
          <HistoryList
            records={records}
            loading={loading}
            onView={viewDetail}
            onDelete={deleteRecord}
            onBacktest={runBacktest}
          />
        )}
        {tab === 'detail' && selected && <HistoryDetail detail={selected} />}
        {tab === 'backtest' && backtestResult && <BacktestView result={backtestResult} />}
      </div>
    </div>
  );
}

/** 历史记录列表 */
function HistoryList({
  records, loading, onView, onDelete, onBacktest,
}: {
  records: HistoryRecord[];
  loading: boolean;
  onView: (id: number) => void;
  onDelete: (id: number) => void;
  onBacktest: (symbol: string) => void;
}) {
  if (loading) return <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t("history.loading")}</div>;
  if (records.length === 0) return <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t("history.empty")}</div>;

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
      <thead>
        <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
          <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.time")}</th>
          <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.stock")}</th>
          <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.market")}</th>
          <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.workflow")}</th>
          <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.agent_count")}</th>
          <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.action")}</th>
        </tr>
      </thead>
      <tbody>
        {records.map((r) => (
          <tr key={r.id} style={{ borderBottom: '1px solid var(--border)' }}>
            <td style={{ padding: '6px 8px', color: 'var(--text-secondary)' }}>
              {new Date(r.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
            </td>
            <td style={{ padding: '6px 8px', fontWeight: 600 }}>{r.symbol}</td>
            <td style={{ padding: '6px 8px' }}>{getMarketLabel(r.market)}</td>
            <td style={{ padding: '6px 8px' }}>{r.workflow}</td>
            <td style={{ padding: '6px 8px' }}>{r.agents.length} 个</td>
            <td style={{ padding: '6px 8px' }}>
              <button onClick={() => onView(r.id)} style={{ ...btnStyle, marginRight: 4 }}>{t("history.view")}</button>
              <button onClick={() => onBacktest(r.symbol)} style={{ ...btnStyle, marginRight: 4, background: '#10b981' }}>{t("history.test")}</button>
              <button onClick={() => onDelete(r.id)} style={{ ...btnStyle, background: '#ef4444' }}>{t("history.delete")}</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** 历史详情 */
function HistoryDetail({ detail }: { detail: HistoryDetail }) {
  return (
    <div style={{ fontSize: 13, color: 'var(--text)' }}>
      <div style={{ marginBottom: 12, display: 'flex', gap: 16, color: 'var(--text-secondary)' }}>
        <span>📊 {detail.symbol}</span>
        <span>{getMarketLabel(detail.market)}</span>
        <span>🔧 {detail.workflow}</span>
        <span>🕐 {new Date(detail.created_at).toLocaleString('zh-CN')}</span>
      </div>

      {/* 各 Agent 意见 */}
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>{t("history.agents_title")}</h3>
        {detail.opinions.map((op: any, i: number) => (
          <div key={i} style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6,
            padding: 10, marginBottom: 8,
          }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>
              {op.agent_name || op.agent_role}
              <span style={{
                marginLeft: 8, fontSize: 11, padding: '1px 6px', borderRadius: 3,
                background: stanceColor(op.stance), color: '#fff',
              }}>
                {op.stance} ({((op.confidence || 0) * 100).toFixed(0)}%)
              </span>
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12, lineHeight: 1.6 }}>
              {op.summary || op.analysis || ''}
            </div>
          </div>
        ))}
      </div>

      {/* 最终报告 Markdown */}
      {detail.markdown && (
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>{t("history.report_title")}</h3>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6,
            padding: 16, fontSize: 13, lineHeight: 1.8,
            color: 'var(--text)', maxHeight: 500, overflow: 'auto',
          }}>
            <Markdown>{detail.markdown}</Markdown>
          </div>
        </div>
      )}
    </div>
  );
}

/** 回测视图 */
function BacktestView({ result }: { result: BacktestResult }) {
  if (!result.records) {
    return <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{result.summary || '无回测数据'}</div>;
  }

  return (
    <div style={{ fontSize: 13, color: 'var(--text)' }}>
      <div style={{ marginBottom: 16, color: 'var(--text-secondary)' }}>
        📊 <strong>{result.symbol}</strong> — 近 {result.days} 天共 {result.records} 次分析，{result.total_predictions} 条预测
      </div>

      <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>各 Agent 预测分布</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
            <th style={{ textAlign: 'left', padding: '6px 8px' }}>Agent</th>
            <th style={{ textAlign: 'center', padding: '6px 8px' }}>预测次数</th>
            <th style={{ textAlign: 'center', padding: '6px 8px' }}>看多</th>
            <th style={{ textAlign: 'center', padding: '6px 8px' }}>看空</th>
            <th style={{ textAlign: 'center', padding: '6px 8px' }}>中性</th>
            <th style={{ textAlign: 'left', padding: '6px 8px' }}>分布</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(result.agent_stats).map(([role, stat]) => {
            const bullish = (stat.stances['bullish'] || 0) + (stat.stances['strong_bullish'] || 0);
            const bearish = (stat.stances['bearish'] || 0) + (stat.stances['strong_bearish'] || 0);
            const neutral = stat.total - bullish - bearish;
            const bullPct = stat.total > 0 ? (bullish / stat.total * 100) : 0;
            const bearPct = stat.total > 0 ? (bearish / stat.total * 100) : 0;
            return (
              <tr key={role} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '6px 8px', fontWeight: 600 }}>{stat.name || role}</td>
                <td style={{ padding: '6px 8px', textAlign: 'center' }}>{stat.total}</td>
                <td style={{ padding: '6px 8px', textAlign: 'center', color: '#10b981' }}>{bullish}</td>
                <td style={{ padding: '6px 8px', textAlign: 'center', color: '#ef4444' }}>{bearish}</td>
                <td style={{ padding: '6px 8px', textAlign: 'center', color: 'var(--text-muted)' }}>{neutral}</td>
                <td style={{ padding: '6px 8px' }}>
                  <div style={{ display: 'flex', height: 12, borderRadius: 3, overflow: 'hidden', background: 'var(--bg-input)' }}>
                    <div style={{ width: `${bullPct}%`, background: '#10b981' }} />
                    <div style={{ width: `${bearPct}%`, background: '#ef4444' }} />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function stanceColor(stance: string): string {
  if (stance?.includes('bullish')) return '#10b981';
  if (stance?.includes('bearish')) return '#ef4444';
  return '#6b7280';
}

const btnStyle: React.CSSProperties = {
  background: '#6366f1', color: '#fff', border: 'none', borderRadius: 3,
  padding: '2px 8px', fontSize: 11, cursor: 'pointer',
};
