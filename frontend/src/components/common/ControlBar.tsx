// frontend/src/components/common/ControlBar.tsx
// 顶部控制栏 — 股票代码输入、市场选择、分析启动按钮、Agent 就绪状态、主题切换

import { useWorkflowStore } from '../../store/workflowStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useTheme } from '../../hooks/useTheme';
import { t } from '../../i18n';

/**
 * ControlBar — 页面顶部控制栏组件
 * 包含：应用标题、股票代码输入框、市场下拉选择、分析按钮、Agent 就绪计数、主题切换
 */
export function ControlBar() {
  const {
    selectedSymbol, setSelectedSymbol, selectedMarket, setSelectedMarket,
    isAnalyzing, nodes,
  } = useWorkflowStore();
  const { sendAnalysis } = useWebSocket();
  const { theme, toggle } = useTheme();

  // 从画布节点中提取所有分析师角色
  const analystRoles = nodes.filter((n) => n.type === 'analyst').map((n) => (n.data as any).role);
  // 构建 Agent 信息列表（包含角色和名称，用于自定义 Agent 传名给后端）
  const agentInfos = nodes.filter((n) => n.type === 'analyst').map((n) => ({
    role: (n.data as any).role,
    name: (n.data as any).label || (n.data as any).role,
  }));

  /** 点击分析按钮 — 通过 WebSocket 发送分析请求 */
  const handleAnalyze = () => {
    if (!selectedSymbol.trim()) return;       // 股票代码不能为空
    if (analystRoles.length === 0) return;    // 至少需要一个分析师
    sendAnalysis(selectedSymbol, selectedMarket, '', analystRoles, agentInfos);
  };

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12, padding: '10px 20px',
      background: 'var(--bg-panel)', borderBottom: '1px solid var(--border)',
      backdropFilter: 'var(--blur)', WebkitBackdropFilter: 'var(--blur)',
    }}>
      {/* 应用标题 */}
      <span style={{
        fontSize: 16, fontWeight: 700, color: 'var(--text)',
        letterSpacing: -0.3,
      }}>TradingFlow</span>

      {/* 股票代码输入框 */}
      <input
        value={selectedSymbol}
        onChange={(e) => setSelectedSymbol(e.target.value)}
        placeholder={t("control.placeholder")}
        style={{
          background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8,
          padding: '6px 12px', color: 'var(--text)', fontSize: 13, width: 200,
          backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
        }}
      />

      {/* 市场类型下拉选择 */}
      <select
        value={selectedMarket}
        onChange={(e) => setSelectedMarket(e.target.value)}
        style={{
          background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8,
          padding: '6px 12px', color: 'var(--text)', fontSize: 13,
          backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
        }}
      >
        <option value="a_share">{t("market.a_share")}</option>
        <option value="h_stock">{t("market.h_stock")}</option>
        <option value="us_stock">{t("market.us_stock")}</option>
      </select>

      {/* 分析按钮 — 分析中时禁用 */}
      <button
        onClick={handleAnalyze}
        disabled={isAnalyzing || !selectedSymbol.trim() || analystRoles.length === 0}
        style={{
          background: isAnalyzing ? 'var(--bg-input)' : 'var(--accent-blue)',
          color: isAnalyzing ? 'var(--text-muted)' : '#fff',
          border: 'none', borderRadius: 8, padding: '6px 20px',
          fontSize: 13, fontWeight: 600, cursor: isAnalyzing ? 'default' : 'pointer',
          opacity: isAnalyzing ? 0.6 : 1,
          boxShadow: isAnalyzing ? 'none' : '0 2px 8px rgba(0, 122, 255, 0.3)',
          transition: 'all 0.2s',
        }}
      >
        {isAnalyzing ? t("control.analyzing") : t("control.start")}
      </button>

      <div style={{ flex: 1 }} />

      {/* 右侧：Agent 就绪计数 */}
      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
        {analystRoles.length} {t("control.agents_ready")}
      </span>

      {/* 主题切换按钮 */}
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
