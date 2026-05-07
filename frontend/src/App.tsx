// frontend/src/App.tsx
// 应用根组件 — 主布局：顶部控制栏 + 标签页切换（工作流编排 / 分析结果）

import { useState, useEffect, Component, type ReactNode } from 'react';
import { Sidebar } from './components/WorkflowEditor/Sidebar';
import { WorkflowEditorCanvas } from './components/WorkflowEditor/Canvas';
import { NodeConfig } from './components/WorkflowEditor/NodeConfig';
import { ControlBar } from './components/common/ControlBar';
import { ReportView } from './components/Analysis/ReportView';
import { TradingViewChart } from './components/TradingView/Chart';
import { HistoryPanel } from './components/History/HistoryPanel';
import { t, loadLocale } from './i18n';
import { WatchlistPanel} from './components/Watchlist/WatchlistPanel';
import { SchedulePanel } from './components/Schedule/SchedulePanel';

/** 错误边界 — 子组件崩溃时显示兜底 UI，不拖垮整个页面 */
class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return <div style={{ padding: 20, color: '#ef4444', fontSize: 13 }}>组件加载失败: {this.state.error.message}</div>;
    }
    return this.props.children;
  }
}

// 标签页类型：workflow（工作流编排）、report（分析结果）、history（历史记录）、watchlist（自选股）、schedule（定时任务）
type Tab = 'workflow' | 'report' | 'history' | 'watchlist' | 'schedule';

export default function App() {
  const [tab, setTab] = useState<Tab>('workflow');
  // 加载语言配置
  useEffect(() => { loadLocale(); }, []);
  // 分析完成后自动切换到结果标签页
  useEffect(() => {
    const handler = () => setTab('report');
    window.addEventListener('switch-to-report', handler);
    return () => window.removeEventListener('switch-to-report', handler);
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg)', color: 'var(--text)' }}>
      {/* 顶部控制栏：股票代码输入、市场选择、分析按钮 */}
      <ControlBar />

      {/* 标签页切换栏 */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', background: 'var(--bg-panel)' }}>
        {(['workflow', 'report', 'history', 'watchlist', 'schedule'] as Tab[]).map((tabKey) => (
          <button
            key={tabKey}
            onClick={() => setTab(tabKey)}
            style={{
              padding: '8px 24px', fontSize: 13, fontWeight: 600,
              background: tab === tabKey ? 'var(--bg-input)' : 'transparent',
              color: tab === tabKey ? 'var(--text)' : 'var(--text-muted)',
              border: 'none', borderBottom: tab === tabKey ? '2px solid #6366f1' : '2px solid transparent',
              cursor: 'pointer',
            }}
          >
            {t(tabKey === 'workflow' ? 'tab.workflow' : tabKey === 'report' ? 'tab.report' : tabKey === 'history' ? 'tab.history' : tabKey === 'watchlist' ? 'tab.watchlist' : 'tab.schedule')}
          </button>
        ))}
      </div>

      {/* 主内容区域 */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {tab === 'workflow' ? (
          <>
            {/* 左侧：Agent 拖拽侧边栏 */}
            <Sidebar />
            {/* 中间：React Flow 画布 */}
            <div style={{ flex: 1, position: 'relative' }}>
              <WorkflowEditorCanvas />
            </div>
            {/* 右侧：节点配置面板 */}
            <NodeConfig />
          </>
        ) : tab === 'report' ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {/* 上方：TradingView K 线图 */}
            <div style={{ flex: '0 0 40%', minHeight: 300, padding: 12 }}>
              <ErrorBoundary>
                <TradingViewChart height={280} />
              </ErrorBoundary>
            </div>
            {/* 下方：分析报告视图 */}
            <div style={{ flex: 1, borderTop: '1px solid var(--border)', overflow: 'auto' }}>
              <ReportView />
            </div>
          </div>
        ) : tab === 'history' ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <HistoryPanel />
          </div>
        ) : tab === 'watchlist' ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <WatchlistPanel />
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <SchedulePanel />
          </div>
        )}
      </div>
    </div>
  );
}
