// frontend/src/components/WorkflowEditor/AgentDetailModal.tsx
// Agent 执行详情弹窗 — 展示单个 Agent 的执行进度、状态和分析结果

import { useWorkflowStore } from '../../store/workflowStore';
import type { AgentOpinion } from '../../types';
import { t } from '../../i18n';

const stanceEmoji: Record<string, string> = {
  bullish: "\u{1F7E2}", bearish: "\u{1F534}", neutral: "\u{1F7E1}",
};

const statusLabel: Record<string, string> = {
  idle: "⏸️", running: "⏳", done: "✅", error: "❌",
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
      background: 'rgba(0,0,0,0.55)', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-strong)',
        borderRadius: 12, width: 520, maxHeight: '80vh', overflow: 'auto',
        boxShadow: "0 0 24px " + color + "44",
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '14px 20px',
          borderBottom: '1px solid var(--border)', background: color + "11",
        }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: color }} />
          <span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)', flex: 1 }}>{label}</span>
          <StatusBadge status={status} />
          <button onClick={onClose} style={{
            background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-muted)',
          }}>{"✕"}</button>
        </div>

        {/* Body */}
        <div style={{ padding: 20 }}>
          {/* Running state: progress messages */}
          {status === 'running' && (
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
                {"⏳"} {t("agent_modal.running")}
              </div>
              {messages.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{t("agent_modal.waiting")}</div>
              ) : (
                <div style={{ maxHeight: 200, overflow: 'auto' }}>
                  {messages.map((msg, i) => (
                    <div key={i} style={{
                      fontSize: 12, color: 'var(--text-secondary)', padding: '4px 0',
                      borderBottom: '1px solid var(--border)',
                    }}>{msg}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Idle state */}
          {status === 'idle' && (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 20 }}>
              {t("agent_modal.idle")}
            </div>
          )}

          {/* Error state */}
          {status === 'error' && (
            <div style={{ color: '#ef4444', fontSize: 13 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>{"❌"} {t("agent_modal.error")}</div>
              {messages.length > 0 && (
                <div style={{ background: '#ef444411', borderRadius: 6, padding: 10, fontSize: 12 }}>
                  {messages[messages.length - 1]}
                </div>
              )}
            </div>
          )}

          {/* Done state: show opinion if available */}
          {status === 'done' && opinion && <OpinionDetail opinion={opinion} color={color} />}

          {/* Done but no opinion yet (still collecting) */}
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

/** StatusBadge — 状态指示标签 */
function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    idle: '#6b7280', running: '#f59e0b', done: '#10b981', error: '#ef4444',
  };
  const c = colorMap[status] || '#6b7280';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: c + "22", color: c,
      borderRadius: 10, padding: '2px 10px', fontSize: 11, fontWeight: 600,
    }}>
      {statusLabel[status] || status} {t("agent_modal.status_" + status) || status}
    </span>
  );
}

/** OpinionDetail — 分析结果详情 */
function OpinionDetail({ opinion, color }: { opinion: AgentOpinion; color: string }) {
  return (
    <div>
      {/* Stance + Confidence */}
      <div style={{
        display: 'flex', gap: 20, alignItems: 'center', marginBottom: 16,
        background: color + "11", borderRadius: 8, padding: '10px 16px',
      }}>
        <span style={{ fontSize: 18 }}>
          {stanceEmoji[opinion.stance] || ""} {t("report.stance_" + opinion.stance) || opinion.stance}
        </span>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>
          {t("report.confidence") || "Confidence"}: {((opinion.confidence || 0) * 100).toFixed(0)}%
        </span>
      </div>

      {/* Summary */}
      {opinion.summary && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t("agent_modal.summary")}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {opinion.summary}
          </div>
        </div>
      )}

      {/* Key Points */}
      {opinion.key_points && opinion.key_points.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t("agent_modal.key_points")}
          </div>
          {opinion.key_points.map((p, i) => (
            <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '2px 0', paddingLeft: 12 }}>
              {"•"} {p}
            </div>
          ))}
        </div>
      )}

      {/* Risk Factors */}
      {opinion.risk_factors && opinion.risk_factors.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#ef4444', marginBottom: 4 }}>
            {t("agent_modal.risk_factors")}
          </div>
          {opinion.risk_factors.map((r, i) => (
            <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '2px 0', paddingLeft: 12 }}>
              {"⚠️"} {r}
            </div>
          ))}
        </div>
      )}

      {/* Data Evidence */}
      {opinion.data_evidence && Object.keys(opinion.data_evidence).length > 0 && (
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t("agent_modal.data_evidence")}
          </div>
          <pre style={{
            fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-input)',
            borderRadius: 6, padding: 10, overflow: 'auto', maxHeight: 150,
          }}>
            {JSON.stringify(opinion.data_evidence, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
