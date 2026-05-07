// frontend/src/components/WorkflowEditor/AgentDetailModal.tsx
// Agent 执行详情弹窗 — 展示单个 Agent 的执行进度、状态和分析结果

import { useWorkflowStore } from '../../store/workflowStore';
import type { AgentOpinion } from '../../types';
import { t } from '../../i18n';

const stanceEmoji: Record<string, string> = {
  bullish: "\u{1F7E2}", bearish: "\u{1F534}", neutral: "\u{1F7E1}",
};

interface Props {
  role: string;
  label: string;
  color: string;
  onClose: () => void;
}

export function AgentDetailModal({ role, label, color, onClose }: Props) {
  const progress = useWorkflowStore((s) => s.agentProgressMap[role]);
  const status = progress?.status || 'idle';
  const messages = progress?.messages || [];
  const opinion = progress?.opinion;

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(0,0,0,0.4)', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--bg-elevated)', border: '1px solid var(--border)',
        borderRadius: 16, width: 520, maxHeight: '80vh', overflow: 'auto',
        boxShadow: 'var(--shadow-elevated)',
        backdropFilter: 'var(--blur-heavy)', WebkitBackdropFilter: 'var(--blur-heavy)',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '14px 20px',
          borderBottom: '1px solid var(--border)',
        }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: color }} />
          <span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)', flex: 1 }}>{label}</span>
          <StatusBadge status={status} />
          <button onClick={onClose} style={{
            background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 8, fontSize: 14, cursor: 'pointer', color: 'var(--text-muted)',
            padding: '2px 8px', lineHeight: 1,
          }}>✕</button>
        </div>

        {/* Body */}
        <div style={{ padding: 20 }}>
          {status === 'running' && (
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-blue)', marginBottom: 8 }}>
                ⏳ {t("agent_modal.running")}
              </div>
              {messages.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{t("agent_modal.waiting")}</div>
              ) : (
                <div style={{ maxHeight: 200, overflow: 'auto' }}>
                  {messages.map((msg, i) => (
                    <div key={i} style={{
                      fontSize: 12, color: 'var(--text-secondary)', padding: '5px 0',
                      borderBottom: '1px solid var(--border)',
                    }}>{msg}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {status === 'idle' && (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 20 }}>
              {t("agent_modal.idle")}
            </div>
          )}

          {status === 'error' && (
            <div style={{ color: 'var(--accent-red)', fontSize: 13 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>❌ {t("agent_modal.error")}</div>
              {messages.length > 0 && (
                <div style={{ background: 'rgba(255,59,48,0.08)', borderRadius: 10, padding: 12, fontSize: 12 }}>
                  {messages[messages.length - 1]}
                </div>
              )}
            </div>
          )}

          {status === 'done' && opinion && <OpinionDetail opinion={opinion} color={color} />}

          {status === 'done' && !opinion && (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 20 }}>
              {t("agent_modal.done_no_result")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    idle: '#8e8e93', running: '#FF9500', done: '#34C759', error: '#FF3B30',
  };
  const c = colorMap[status] || '#8e8e93';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: `${c}18`, color: c,
      borderRadius: 8, padding: '3px 10px', fontSize: 11, fontWeight: 600,
    }}>
      {t("agent_modal.status_" + status) || status}
    </span>
  );
}

function OpinionDetail({ opinion, color }: { opinion: AgentOpinion; color: string }) {
  return (
    <div>
      <div style={{
        display: 'flex', gap: 24, alignItems: 'center', marginBottom: 16,
        background: `${color}10`, borderRadius: 10, padding: '12px 16px',
      }}>
        <span style={{ fontSize: 16 }}>
          {stanceEmoji[opinion.stance] || ""} {t("report.stance_" + opinion.stance) || opinion.stance}
        </span>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-blue)' }}>
          {t("report.confidence") || "Confidence"}: {((opinion.confidence || 0) * 100).toFixed(0)}%
        </span>
      </div>

      {opinion.summary && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t("agent_modal.summary")}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            {opinion.summary}
          </div>
        </div>
      )}

      {opinion.key_points && opinion.key_points.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t("agent_modal.key_points")}
          </div>
          {opinion.key_points.map((p, i) => (
            <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '3px 0', paddingLeft: 14 }}>• {p}</div>
          ))}
        </div>
      )}

      {opinion.risk_factors && opinion.risk_factors.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-red)', marginBottom: 4 }}>
            {t("agent_modal.risk_factors")}
          </div>
          {opinion.risk_factors.map((r, i) => (
            <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '3px 0', paddingLeft: 14 }}>⚠️ {r}</div>
          ))}
        </div>
      )}

      {opinion.data_evidence && Object.keys(opinion.data_evidence).length > 0 && (
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t("agent_modal.data_evidence")}
          </div>
          <pre style={{
            fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-input)',
            borderRadius: 10, padding: 12, overflow: 'auto', maxHeight: 150,
            border: '1px solid var(--border)',
          }}>
            {JSON.stringify(opinion.data_evidence, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
