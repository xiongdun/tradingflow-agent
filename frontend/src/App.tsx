// frontend/src/App.tsx
// 应用根组件 — 主布局：顶部控制栏 + 标签页切换（工作流编排 / 分析结果）

import { useState, useEffect, useCallback, useRef, Component, type ReactNode, lazy, Suspense } from 'react';
import { Sidebar } from './components/WorkflowEditor/Sidebar';
import { WorkflowEditorCanvas } from './components/WorkflowEditor/Canvas';
import { NodeConfig } from './components/WorkflowEditor/NodeConfig';
import { ControlBar } from './components/common/ControlBar';
import { ToastContainer } from './components/common/Toast';
import { t, loadLocale } from './i18n';

const ReportView = lazy(() => import('./components/Analysis/ReportView').then(m => ({ default: m.ReportView })));
const TradingViewChart = lazy(() => import('./components/TradingView/Chart').then(m => ({ default: m.TradingViewChart })));
const HistoryPanel = lazy(() => import('./components/History/HistoryPanel').then(m => ({ default: m.HistoryPanel })));
const WatchlistPanel = lazy(() => import('./components/Watchlist/WatchlistPanel').then(m => ({ default: m.WatchlistPanel })));
const SchedulePanel = lazy(() => import('./components/Schedule/SchedulePanel').then(m => ({ default: m.SchedulePanel })));

/** 可拖拽调整宽度的面板容器 */
function ResizablePanel({
  children, defaultWidth, minWidth = 160, maxWidth = 440, position = 'left',
}: {
  children: React.ReactNode;
  defaultWidth: number;
  minWidth?: number;
  maxWidth?: number;
  position?: 'left' | 'right';
}) {
  const [width, setWidth] = useState(defaultWidth);
  const dragging = useRef(false);
  const startX = useRef(0);
  const startW = useRef(0);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;
    startX.current = e.clientX;
    startW.current = width;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      const dx = ev.clientX - startX.current;
      const newW = Math.min(maxWidth, Math.max(minWidth, position === 'left' ? startW.current + dx : startW.current - dx));
      setWidth(newW);
    };
    const onUp = () => {
      dragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [width, minWidth, maxWidth, position]);

  return (
    <div style={{ width, minWidth, flexShrink: 0, display: 'flex', position: 'relative', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'hidden' }}>{children}</div>
      <div
        onMouseDown={onMouseDown}
        style={{
          width: 5, cursor: 'col-resize', flexShrink: 0,
          background: 'transparent', transition: 'background 0.2s',
          zIndex: 10,
        }}
        onMouseEnter={(e) => { (e.target as HTMLElement).style.background = 'rgba(99,102,241,0.3)'; }}
        onMouseLeave={(e) => { if (!dragging.current) (e.target as HTMLElement).style.background = 'transparent'; }}
      />
    </div>
  );
}

/** 错误边界 — 子组件崩溃时显示兜底 UI + 重试按钮，不拖垮整个页面 */
class ErrorBoundary extends Component<
  { children: ReactNode; label?: string },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      const label = this.props.label || '组件';
      return (
        <div style={{ padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <div style={{ color: 'var(--accent-red)', fontSize: 14, fontWeight: 600 }}>
            {label}加载失败
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: 12, maxWidth: 400, textAlign: 'center', wordBreak: 'break-all' }}>
            {this.state.error.message}
          </div>
          <button
            onClick={() => this.setState({ error: null })}
            style={{
              background: 'var(--accent-blue)', color: '#fff', border: 'none',
              borderRadius: 6, padding: '6px 16px', fontSize: 12, cursor: 'pointer',
            }}
          >
            重试
          </button>
        </div>
      );
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
      <ToastContainer />
      {/* 顶部控制栏：股票代码输入、市场选择、分析按钮 */}
      <ControlBar />

      {/* 标签页切换栏 */}
      <div style={{
        display: 'flex', borderBottom: '1px solid var(--border)', background: 'var(--bg-panel)',
        backdropFilter: 'var(--blur)', WebkitBackdropFilter: 'var(--blur)',
      }}>
        {(['workflow', 'report', 'history', 'watchlist', 'schedule'] as Tab[]).map((tabKey) => (
          <button
            key={tabKey}
            onClick={() => setTab(tabKey)}
            style={{
              padding: '8px 24px', fontSize: 13, fontWeight: tab === tabKey ? 600 : 400,
              background: tab === tabKey ? 'var(--bg-elevated)' : 'transparent',
              color: tab === tabKey ? 'var(--text)' : 'var(--text-muted)',
              border: 'none',
              borderBottom: tab === tabKey ? '2px solid var(--accent-blue)' : '2px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {t(tabKey === 'workflow' ? 'tab.workflow' : tabKey === 'report' ? 'tab.report' : tabKey === 'history' ? 'tab.history' : tabKey === 'watchlist' ? 'tab.watchlist' : 'tab.schedule')}
          </button>
        ))}
      </div>

      {/* 主内容区域 */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {tab === 'workflow' ? (
          <ErrorBoundary label="工作流编辑">
            <>
              <ResizablePanel defaultWidth={240} minWidth={180} maxWidth={400} position="left">
                <Sidebar />
              </ResizablePanel>
              <div style={{ flex: 1, position: 'relative' }}>
                <WorkflowEditorCanvas />
              </div>
              <ResizablePanel defaultWidth={320} minWidth={240} maxWidth={500} position="right">
                <NodeConfig />
              </ResizablePanel>
            </>
          </ErrorBoundary>
        ) : tab === 'report' ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ flex: '0 0 40%', minHeight: 300, padding: 12 }}>
              <ErrorBoundary label="K线图表">
                <Suspense fallback={<div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</div>}>
                  <TradingViewChart height={280} />
                </Suspense>
              </ErrorBoundary>
            </div>
            <div style={{ flex: 1, borderTop: '1px solid var(--border)', overflow: 'auto' }}>
              <ErrorBoundary label="分析报告">
                <Suspense fallback={<div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</div>}>
                  <ReportView />
                </Suspense>
              </ErrorBoundary>
            </div>
          </div>
        ) : tab === 'history' ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <ErrorBoundary label="历史记录">
              <Suspense fallback={<div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</div>}>
                <HistoryPanel />
              </Suspense>
            </ErrorBoundary>
          </div>
        ) : tab === 'watchlist' ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <ErrorBoundary label="自选股">
              <Suspense fallback={<div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</div>}>
                <WatchlistPanel />
              </Suspense>
            </ErrorBoundary>
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <ErrorBoundary label="定时任务">
              <Suspense fallback={<div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</div>}>
                <SchedulePanel />
              </Suspense>
            </ErrorBoundary>
          </div>
        )}
      </div>
    </div>
  );
}
