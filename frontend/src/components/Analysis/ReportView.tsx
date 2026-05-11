// frontend/src/components/Analysis/ReportView.tsx
// 分析报告视图

import { useWorkflowStore } from '../../store/workflowStore';
import { t } from '../../i18n';
import AgentRadarChart from './AgentRadarChart';
import StancePieChart from './StancePieChart';

const getStanceEmoji = (s: string) => t(`report.stance_${s}`) || s;
const STANCE_BG: Record<string, string> = { bullish: 'rgba(52,199,89,0.08)', bearish: 'rgba(255,59,48,0.08)', neutral: 'rgba(255,149,0,0.08)' };
const getActionLabel = (a: string) => t(`report.action_${a}`) || a;

export function ReportView() {
  const { finalReport, opinions, isAnalyzing, analysisProgress } = useWorkflowStore();

  if (isAnalyzing) {
    return (
      <div style={{ padding: 24, color: 'var(--text-secondary)' }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', marginBottom: 16 }}>{t("report.analyzing")}</div>
        {analysisProgress.map((msg, i) => (
          <div key={i} style={{
            fontSize: 13, padding: '6px 0', borderBottom: '1px solid var(--border)',
          }}>{msg}</div>
        ))}
      </div>
    );
  }

  if (!finalReport) {
    return (
      <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.4 }}>📊</div>
        <div style={{ fontSize: 14 }}>{t("report.empty")}</div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <ExportBar />
      <div style={{
        background: STANCE_BG[finalReport.overall_stance] || 'var(--bg-input)',
        border: '1px solid var(--border)', borderRadius: 14, padding: 20, marginBottom: 20,
        backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)', marginBottom: 10 }}>
          {finalReport.stock} ({finalReport.market})
        </div>
        <div style={{ display: 'flex', gap: 24, fontSize: 14 }}>
          <span>{getStanceEmoji(finalReport.overall_stance)}</span>
          <span style={{ color: 'var(--text-secondary)' }}>{t("report.confidence") || "Confidence"}: <strong style={{ color: 'var(--accent-blue)' }}>{((finalReport.overall_confidence || 0) * 100).toFixed(0)}%</strong></span>
          <span style={{ fontWeight: 700, color: 'var(--accent-green)' }}>{getActionLabel(finalReport.action_suggestion)}</span>
        </div>
      </div>

      {finalReport.consensus_points?.length > 0 && (
        <Section title={t("report.consensus")} items={finalReport.consensus_points} />
      )}
      {finalReport.disagreement_points?.length > 0 && (
        <Section title={t("report.disagreement")} items={finalReport.disagreement_points} />
      )}
      {finalReport.key_risks?.length > 0 && (
        <Section title={t("report.risks")} items={finalReport.key_risks} color="var(--accent-red)" />
      )}
      {finalReport.opportunities?.length > 0 && (
        <Section title={t("report.opportunities")} items={finalReport.opportunities} color="var(--accent-green)" />
      )}

      <div style={{
        marginTop: 16, padding: 18, background: 'var(--bg-card)', borderRadius: 12,
        color: 'var(--text-subtle)', fontSize: 14, lineHeight: 1.7,
        border: '1px solid var(--border)',
        backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
      }}>
        {finalReport.summary || t("report.no_summary")}
      </div>

      {(opinions.length > 0 || finalReport.agent_opinions?.length > 0) && (
        <div style={{ display: 'flex', gap: 16, marginTop: 20, flexWrap: 'wrap' }}>
          <AgentRadarChart opinions={opinions.length > 0 ? opinions : finalReport.agent_opinions} />
          <StancePieChart opinions={opinions.length > 0 ? opinions : finalReport.agent_opinions} />
        </div>
      )}

      {(opinions.length > 0 || finalReport.agent_opinions?.length > 0) && (
        <div style={{ marginTop: 20 }}>
          <h3 style={{ color: 'var(--text)', fontSize: 16, marginBottom: 12, fontWeight: 600 }}>{t("report.agents_title")}</h3>
          {(opinions.length > 0 ? opinions : finalReport.agent_opinions).map((op: AgentOpinion, i: number) => <OpinionCard key={i} opinion={op} />)}
        </div>
      )}
    </div>
  );
}

function Section({ title, items, color }: { title: string; items: string[]; color?: string }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>{title}</div>
      {items.map((item, i) => (
        <div key={i} style={{
          fontSize: 13, color: color || 'var(--text-secondary)', padding: '4px 0', paddingLeft: 14,
          borderLeft: '2px solid var(--border)', marginLeft: 4, marginBottom: 4,
        }}>• {item}</div>
      ))}
    </div>
  );
}

type AgentOpinion = import('../../types').AgentOpinion;

function OpinionCard({ opinion }: { opinion: AgentOpinion }) {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12,
      padding: 14, marginBottom: 10,
      backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 14 }}>{opinion.agent_name}</span>
        <span style={{ fontSize: 12, color: 'var(--accent-blue)' }}>
          {getStanceEmoji(opinion.stance)} ({(opinion.confidence * 100).toFixed(0)}%)
        </span>
      </div>
      {opinion.key_points.length > 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          {opinion.key_points.map((p, i) => <div key={i} style={{ padding: '2px 0' }}>• {p}</div>)}
        </div>
      )}
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{opinion.summary}</div>
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  background: 'var(--bg-card)', color: 'var(--accent-blue)', border: '1px solid var(--border)',
  borderRadius: 8, padding: '5px 14px', fontSize: 12, cursor: 'pointer', fontWeight: 500,
  backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
  transition: 'all 0.2s',
};

function ExportBar() {
  const handleExport = (format: 'md' | 'html' | 'txt') => {
    const a = document.createElement('a');
    a.href = `/api/export/latest?format=${format}`;
    a.download = `report.${format === 'md' ? 'md' : format === 'html' ? 'html' : 'txt'}`;
    a.click();
  };

  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 16, justifyContent: 'flex-end' }}>
      <span style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: '30px' }}>{t("report.export")}</span>
      <button onClick={() => handleExport('md')} style={btnStyle}>📄 Markdown</button>
      <button onClick={() => handleExport('html')} style={{ ...btnStyle, color: 'var(--accent-green)' }}>🌐 HTML</button>
      <button onClick={() => handleExport('txt')} style={{ ...btnStyle, color: 'var(--text-muted)' }}>📝 纯文本</button>
    </div>
  );
}

export default ReportView;