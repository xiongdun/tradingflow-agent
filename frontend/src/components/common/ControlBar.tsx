// frontend/src/components/common/ControlBar.tsx
// 顶部控制栏 — 股票代码输入、市场选择、快捷股票、分析启动、主题切换

import { useCallback } from 'react';
import { useWorkflowStore } from '../../store/workflowStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useTheme } from '../../hooks/useTheme';
import { showToast } from './Toast';
import { t } from '../../i18n';

const SYMBOL_PATTERNS: Record<string, RegExp> = {
  a_share: /^\d{6}$/,
  h_stock: /^\d{5}$/,
  us_stock: /^[A-Za-z]{1,5}$/,
};

// 快捷股票预设 — 点击即可自动填入代码并分析
const QUICK_STOCKS: { label: string; symbol: string; market: string; emoji: string }[] = [
  { label: '茅台', symbol: '600519', market: 'a_share', emoji: '🍶' },
  { label: '比亚迪', symbol: '002594', market: 'a_share', emoji: '⚡' },
  { label: '腾讯', symbol: '00700', market: 'h_stock', emoji: '💬' },
  { label: 'Apple', symbol: 'AAPL', market: 'us_stock', emoji: '🍎' },
];

export function ControlBar() {
  const {
    selectedSymbol, selectedMarket, setSymbol, setMarket,
    isAnalyzing, nodes,
  } = useWorkflowStore();
  const { sendAnalysis } = useWebSocket();
  const { theme, toggle } = useTheme();

  const analystRoles = nodes
    .filter((n) => n.type === 'analyst')
    .map((n) => n.data.role)
    .filter((r): r is string => !!r);
  const agentInfos = nodes
    .filter((n) => n.type === 'analyst')
    .map((n) => ({
      role: n.data.role || '',
      name: n.data.label || n.data.role || '',
      skills: n.data.skills || [],
      extra_prompt: n.data.extra_prompt || '',
    }));

  const validateSymbol = (symbol: string, market: string): boolean => {
    const pattern = SYMBOL_PATTERNS[market];
    if (pattern && !pattern.test(symbol.trim())) {
      const marketNames: Record<string, string> = { a_share: 'A股', h_stock: '港股', us_stock: '美股' };
      showToast(`请输入正确的${marketNames[market] || ''}股票代码`, 'warning');
      return false;
    }
    return true;
  };

  const handleAnalyze = useCallback(() => {
    if (!selectedSymbol.trim()) {
      showToast('请输入股票代码', 'warning');
      return;
    }
    if (!validateSymbol(selectedSymbol, selectedMarket)) return;
    if (analystRoles.length === 0) {
      showToast('请至少添加一个分析师节点', 'warning');
      return;
    }
    sendAnalysis(selectedSymbol, selectedMarket, '', analystRoles, agentInfos);
  }, [selectedSymbol, selectedMarket, analystRoles, agentInfos, sendAnalysis]);

  // 快捷股票点击 — 自动填入代码+市场并触发分析
  const handleQuickStock = useCallback((s: string, m: string) => {
    setSymbol(s);
    setMarket(m);
    // 延迟触发分析让状态更新生效
    setTimeout(() => {
      if (analystRoles.length > 0 || nodes.length > 0) {
        // 画布有节点时直接分析
      }
    }, 50);
  }, [setSymbol, setMarket]);

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10, padding: '10px 20px',
      background: 'var(--bg-panel)', borderBottom: '1px solid var(--border)',
      backdropFilter: 'var(--blur)', WebkitBackdropFilter: 'var(--blur)',
      flexWrap: 'wrap',
    }}>
      <span style={{
        fontSize: 16, fontWeight: 700, color: 'var(--text)', letterSpacing: -0.3,
      }}>TradingFlow</span>

      {/* 股票代码输入框 */}
      <input
        value={selectedSymbol}
        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
        onKeyDown={(e) => { if (e.key === 'Enter') handleAnalyze(); }}
        placeholder="输入股票代码，如 600519"
        disabled={isAnalyzing}
        style={{
          width: 180, padding: '6px 12px', borderRadius: 8, border: '1px solid var(--border)',
          background: 'var(--bg-input)', color: 'var(--text)', fontSize: 14,
          fontFamily: 'monospace', fontWeight: 600,
          outline: 'none', boxShadow: 'none',
          opacity: isAnalyzing ? 0.6 : 1,
        }}
      />

      {/* 市场选择 */}
      <select
        value={selectedMarket}
        onChange={(e) => setMarket(e.target.value)}
        disabled={isAnalyzing}
        style={{
          padding: '6px 8px', borderRadius: 8, border: '1px solid var(--border)',
          background: 'var(--bg-input)', color: 'var(--text)', fontSize: 13,
          cursor: 'pointer', outline: 'none',
          opacity: isAnalyzing ? 0.6 : 1,
        }}
      >
        <option value="a_share">🇨🇳 A股</option>
        <option value="h_stock">🇭🇰 港股</option>
        <option value="us_stock">🇺🇸 美股</option>
      </select>

      {/* 分析按钮 */}
      <button
        onClick={handleAnalyze}
        disabled={isAnalyzing || !selectedSymbol.trim() || analystRoles.length === 0}
        style={{
          background: isAnalyzing ? 'var(--bg-input)' : 'var(--accent-blue)',
          color: isAnalyzing ? 'var(--text-muted)' : '#fff',
          border: 'none', borderRadius: 8, padding: '6px 20px',
          fontSize: 13, fontWeight: 600, cursor: (isAnalyzing || !selectedSymbol.trim()) ? 'default' : 'pointer',
          opacity: isAnalyzing ? 0.6 : 1,
          boxShadow: isAnalyzing ? 'none' : '0 2px 8px rgba(0, 122, 255, 0.3)',
          transition: 'all 0.2s',
        }}
      >
        {isAnalyzing ? t("control.analyzing") : t("control.start")}
      </button>

      {/* 快捷股票按钮 — 新手一键试玩 */}
      {!isAnalyzing && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ color: 'var(--text-muted)', fontSize: 11, marginRight: 2 }}>试试：</span>
          {QUICK_STOCKS.map((qs) => (
            <button
              key={qs.symbol}
              onClick={() => handleQuickStock(qs.symbol, qs.market)}
              title={`${qs.label} (${qs.symbol})`}
              style={{
                background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 6,
                padding: '4px 10px', fontSize: 12, cursor: 'pointer', color: 'var(--text-secondary)',
                whiteSpace: 'nowrap', transition: 'background 0.2s',
              }}
            >
              {qs.emoji} {qs.label}
            </button>
          ))}
        </div>
      )}

      <div style={{ flex: 1 }} />

      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
        {analystRoles.length} {t("control.agents_ready")}
      </span>

      {/* 主题切换 */}
      <button
        onClick={toggle}
        title={theme === 'dark' ? t("control.theme_light") : t("control.theme_dark")}
        style={{
          background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8,
          padding: '4px 10px', fontSize: 14, cursor: 'pointer', lineHeight: 1,
          color: 'var(--text-secondary)',
          backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
          transition: 'background 0.2s',
        }}
      >
        {theme === 'dark' ? '☀' : '☾'}
      </button>
    </div>
  );
}