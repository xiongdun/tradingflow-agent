// frontend/src/App.tsx
// 应用根组件 — 主布局：顶部控制栏 + 标签页切换（工作流编排 / 分析结果）

import { useState, useEffect, useCallback, useRef, Component, type ReactNode } from 'react';
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

/** 错误边界 — 子组件崩溃时显示兜底 UI，不拖垮整个页面 */
class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return <div style={{ padding: 20, color: 'var(--accent-red)', fontSize: 13 }}>组件加载失败: {this.state.error.message}</div>;
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
          <>
            {/* 左侧：Agent 拖拽侧边栏（可拖拽调整宽度） */}
            <ResizablePanel defaultWidth={240} minWidth={180} maxWidth={400} position="left">
              <Sidebar />
            </ResizablePanel>
            {/* 中间：React Flow 画布 */}
            <div style={{ flex: 1, position: 'relative' }}>
              <WorkflowEditorCanvas />
            </div>
            {/* 右侧：节点配置面板（可拖拽调整宽度） */}
            <ResizablePanel defaultWidth={320} minWidth={240} maxWidth={500} position="right">
              <NodeConfig />
            </ResizablePanel>
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
