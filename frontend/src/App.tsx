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
const SettingsPanel = lazy(() => import('./components/Settings/SettingsPanel').then(m => ({ default: m.SettingsPanel })));

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

// 标签页类型：workflow（工作流编排）、report（分析结果）、history（历史记录）、watchlist（自选股）、schedule（定时任务）、settings（系统设置）
type Tab = 'workflow' | 'report' | 'history' | 'watchlist' | 'schedule' | 'settings';

const ONBOARDING_KEY = 'tradingflow_onboarding_done_v1';

function OnboardingModal({ onDismiss }: { onDismiss: (dontShowAgain: boolean) => void }) {
  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onDismiss(false); }}
      style={{
        position: 'fixed', inset: 0, zIndex: 10000,
        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      <div style={{
        background: 'var(--bg-panel)', borderRadius: 16, padding: '28px 32px',
        maxWidth: 520, width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
        border: '1px solid var(--border)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>🤖</div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text)' }}>
            欢迎使用 TradingFlow Agent
          </h2>
          <p style={{ margin: '6px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>
            AI 多智能体股票分析系统 — 快速上手只需 3 步
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[
            { emoji: '1️⃣', title: '输入股票代码', desc: '在上方搜索框输入代码（如 600519），或点击快捷按钮' },
            { emoji: '2️⃣', title: '点击分析', desc: '选择市场（A股/港股/美股），点击「开始分析」' },
            { emoji: '3️⃣', title: '查看结果', desc: 'AI 自动生成多维度分析报告 + K线图表' },
          ].map((step) => (
            <div
              key={step.title}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '6px 0',
              }}
            >
              <span style={{ fontSize: 20, flexShrink: 0 }}>{step.emoji}</span>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>{step.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{step.desc}</div>
              </div>
            </div>
          ))}
        </div>

        <div style={{
          marginTop: 20, padding: '12px 14px',
          background: 'var(--bg-input)', borderRadius: 10,
          fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6,
        }}>
          💡 <strong>提示：</strong>可在下方「工作流编排」中自由拖拽组合 Agent，也可在「预置模板」中一键加载高频策略。
        </div>

        <div style={{
          display: 'flex', gap: 10, marginTop: 20,
          justifyContent: 'space-between', alignItems: 'center',
        }}>
          <label style={{
            display: 'flex', alignItems: 'center', gap: 6,
            fontSize: 12, color: 'var(--text-muted)', cursor: 'pointer',
          }}>
            <input
              type="checkbox"
              onChange={(e) => {
                if (e.target.checked) {
                  localStorage.setItem(ONBOARDING_KEY, '1');
                }
              }}
              style={{ accentColor: 'var(--accent-blue)' }}
            />
            不再显示
          </label>
          <button
            onClick={() => onDismiss(false)}
            style={{
              background: 'var(--accent-blue)', color: '#fff', border: 'none',
              borderRadius: 10, padding: '10px 32px', fontSize: 14, fontWeight: 600,
              cursor: 'pointer', boxShadow: '0 4px 16px rgba(0,122,255,0.3)',
            }}
          >
            开始使用
          </button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>('workflow');
  const [showOnboarding, setShowOnboarding] = useState(() => {
    return !localStorage.getItem(ONBOARDING_KEY);
  });
  useEffect(() => { loadLocale(); }, []);
  useEffect(() => {
    const handler = () => setTab('report');
    window.addEventListener('switch-to-report', handler);
    return () => window.removeEventListener('switch-to-report', handler);
  }, []);

  const dismissOnboarding = (dontShowAgain: boolean) => {
    setShowOnboarding(false);
    if (dontShowAgain || true) {
      localStorage.setItem(ONBOARDING_KEY, '1');
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg)', color: 'var(--text)' }}>
      <ToastContainer />
      {showOnboarding && <OnboardingModal onDismiss={dismissOnboarding} />}
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
        {/* 分隔线 */}
        <div style={{ width: 1, background: 'var(--border)', margin: '6px 0' }} />
        {/* 系统设置按钮 */}
        <button
          onClick={() => setTab('settings')}
          style={{
            padding: '8px 16px', fontSize: 13, fontWeight: tab === 'settings' ? 600 : 400,
            background: tab === 'settings' ? 'var(--bg-elevated)' : 'transparent',
            color: tab === 'settings' ? 'var(--text)' : 'var(--text-muted)',
            border: 'none',
            borderBottom: tab === 'settings' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          ⚙️ {t('tab.settings')}
        </button>
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
        ) : tab === 'schedule' ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <ErrorBoundary label="定时任务">
              <Suspense fallback={<div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</div>}>
                <SchedulePanel />
              </Suspense>
            </ErrorBoundary>
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <ErrorBoundary label="系统设置">
              <Suspense fallback={<div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</div>}>
                <SettingsPanel />
              </Suspense>
            </ErrorBoundary>
          </div>
        )}
      </div>
    </div>
  );
}
