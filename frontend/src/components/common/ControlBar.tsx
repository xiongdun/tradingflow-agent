// frontend/src/components/common/ControlBar.tsx
// 顶部控制栏 — 股票代码输入、市场选择、分析启动按钮、Agent 就绪状态、主题切换

import { useWorkflowStore } from '../../store/workflowStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useTheme } from '../../hooks/useTheme';
import { showToast } from './Toast';
import { t } from '../../i18n';

// 股票代码正则：A股 6 位数字、港股 5 位数字、美股 1~5 位字母
const SYMBOL_PATTERNS: Record<string, RegExp> = {
  a_share: /^\d{6}$/,
  h_stock: /^\d{5}$/,
  us_stock: /^[A-Za-z]{1,5}$/,
};

/**
 * ControlBar — 页面顶部控制栏组件
 * 包含：应用标题、股票代码输入框、市场下拉选择、分析按钮、Agent 就绪计数、主题切换
 */
export function ControlBar() {
  const {
    selectedSymbol, selectedMarket,
    isAnalyzing, nodes,
  } = useWorkflowStore();
  const { sendAnalysis } = useWebSocket();
  const { theme, toggle } = useTheme();

  // 从画布节点中提取所有分析师角色（类型安全）
  const analystRoles = nodes
    .filter((n) => n.type === 'analyst')
    .map((n) => n.data.role)
    .filter((r): r is string => !!r);
  // 构建 Agent 信息列表（包含角色和名称，用于自定义 Agent 传名给后端）
  const agentInfos = nodes
    .filter((n) => n.type === 'analyst')
    .map((n) => ({
      role: n.data.role || '',
      name: n.data.label || n.data.role || '',
      skills: n.data.skills || [],
      extra_prompt: n.data.extra_prompt || '',
    }));

  /** 校验股票代码格式 */
  const validateSymbol = (symbol: string, market: string): boolean => {
    const pattern = SYMBOL_PATTERNS[market];
    if (pattern && !pattern.test(symbol.trim())) {
      const marketNames: Record<string, string> = { a_share: 'A股', h_stock: '港股', us_stock: '美股' };
      showToast(`请输入正确的${marketNames[market] || ''}股票代码`, 'warning');
      return false;
    }
    return true;
  };

  /** 点击分析按钮 — 通过 WebSocket 发送分析请求 */
  const handleAnalyze = () => {
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

      {/* 当前股票代码提示（从画布 InputNode 同步） */}
      {selectedSymbol && (
        <span style={{
          background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8,
          padding: '6px 12px', color: 'var(--accent-green)', fontSize: 13, fontWeight: 600,
          fontFamily: 'monospace',
        }}>
          {selectedSymbol}
          <span style={{ color: 'var(--text-muted)', fontSize: 11, marginLeft: 6 }}>
            {selectedMarket === 'a_share' ? 'A股' : selectedMarket === 'us_stock' ? '美股' : '港股'}
          </span>
        </span>
      )}

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
