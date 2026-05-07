// frontend/src/components/Analysis/ReportView.tsx
// 分析报告视图 — 展示综合研判结果、共识/分歧/风险/机会、各分析师详细观点
// 含导出按钮（MD/HTML/TXT）和 SVG 可视化（置信度雷达图 + 立场饼图）

import { useWorkflowStore } from '../../store/workflowStore';
import type { AgentOpinion } from '../../types';
import { t } from '../../i18n';

// 立场标签映射（含 emoji）
const getStanceEmoji = (s: string) => t(`report.stance_${s}`) || s;
// 立场背景色映射
const STANCE_BG: Record<string, string> = { bullish: '#10b98122', bearish: '#ef444422', neutral: '#f59e0b22' };
// 投资建议标签映射
const getActionLabel = (a: string) => t(`report.action_${a}`) || a;

/**
 * ReportView — 分析报告主视图组件
 * 三种状态：分析中（进度条）、无结果（占位提示）、有结果（完整报告）
 */
export function ReportView() {
  const { finalReport, opinions, isAnalyzing, analysisProgress } = useWorkflowStore();

  // 分析进行中 — 显示实时进度消息
  if (isAnalyzing) {
    return (
      <div style={{ padding: 20, color: 'var(--text-secondary)' }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', marginBottom: 12 }}>{t("report.analyzing")}</div>
        {analysisProgress.map((msg, i) => (
          <div key={i} style={{ fontSize: 13, padding: '3px 0', borderBottom: '1px solid var(--border)' }}>{msg}</div>
        ))}
      </div>
    );
  }

  // 无分析结果 — 显示空状态占位提示
  if (!finalReport) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>📊</div>
        <div style={{ fontSize: 14 }}>{t("report.empty")}</div>
      </div>
    );
  }

  // 有分析结果 — 展示完整报告
  return (
    <div style={{ padding: 20 }}>
      {/* 导出按钮栏 */}
      <ExportBar />

      {/* 综合研判摘要卡片 */}
      <div style={{
        background: STANCE_BG[finalReport.overall_stance] || 'var(--bg-input)', border: '1px solid var(--border-strong)',
        borderRadius: 12, padding: 20, marginBottom: 20,
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>
          {finalReport.stock} ({finalReport.market})
        </div>
        <div style={{ display: 'flex', gap: 20, fontSize: 14 }}>
          <span>{getStanceEmoji(finalReport.overall_stance)}</span>
          <span>t("report.confidence") || "Confidence": {((finalReport.overall_confidence || 0) * 100).toFixed(0)}%</span>
          <span style={{ fontWeight: 700 }}>{getActionLabel(finalReport.action_suggestion)}</span>
        </div>
      </div>

      {/* 分析师共识 / 分歧 / 风险 / 机会 各区块 */}
      {finalReport.consensus_points?.length > 0 && (
        <Section title={t("report.consensus")} items={finalReport.consensus_points} />
      )}
      {finalReport.disagreement_points?.length > 0 && (
        <Section title={t("report.disagreement")} items={finalReport.disagreement_points} />
      )}
      {finalReport.key_risks?.length > 0 && (
        <Section title={t("report.risks")} items={finalReport.key_risks} color="#ef4444" />
      )}
      {finalReport.opportunities?.length > 0 && (
        <Section title={t("report.opportunities")} items={finalReport.opportunities} color="#22c55e" />
      )}

      {/* 综合分析总结文本 */}
      <div style={{ marginTop: 16, padding: 16, background: 'var(--bg-card)', borderRadius: 8, color: 'var(--text-subtle)', fontSize: 14, lineHeight: 1.7 }}>
        {finalReport.summary || t("report.no_summary")}
      </div>

      {/* SVG 可视化图表 */}
      {(opinions.length > 0 || finalReport.agent_opinions?.length > 0) && (
        <div style={{ display: 'flex', gap: 20, marginTop: 20, flexWrap: 'wrap' }}>
          <AgentRadarChart opinions={opinions.length > 0 ? opinions : finalReport.agent_opinions} />
          <StancePieChart opinions={opinions.length > 0 ? opinions : finalReport.agent_opinions} />
        </div>
      )}

      {/* 各分析师详细观点卡片列表 */}
      {(opinions.length > 0 || finalReport.agent_opinions?.length > 0) && (
        <div style={{ marginTop: 20 }}>
          <h3 style={{ color: 'var(--text)', fontSize: 16, marginBottom: 12 }}>{t("report.agents_title")}</h3>
          {(opinions.length > 0 ? opinions : finalReport.agent_opinions).map((op: any, i: number) => <OpinionCard key={i} opinion={op} />)}
        </div>
      )}
    </div>
  );
}

/**
 * Section — 通用列表区块组件（共识、分歧、风险、机会）
 * @param title 区块标题
 * @param items 列表项内容
 * @param color 可选的文字颜色
 */
function Section({ title, items, color }: { title: string; items: string[]; color?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>{title}</div>
      {items.map((item, i) => (
        <div key={i} style={{ fontSize: 13, color: color || 'var(--text-secondary)', padding: '2px 0', paddingLeft: 12 }}>• {item}</div>
      ))}
    </div>
  );
}

/**
 * OpinionCard — 单个分析师意见卡片
 * 展示分析师名称、立场、置信度、核心论点和总结
 */
function OpinionCard({ opinion }: { opinion: AgentOpinion }) {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-strong)', borderRadius: 8,
      padding: 14, marginBottom: 10,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 14 }}>{opinion.agent_name}</span>
        <span style={{ fontSize: 12 }}>
          {getStanceEmoji(opinion.stance)} ({(opinion.confidence * 100).toFixed(0)}%)
        </span>
      </div>
      {/* 核心论点列表 */}
      {opinion.key_points.length > 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          {opinion.key_points.map((p, i) => <div key={i} style={{ padding: '1px 0' }}>• {p}</div>)}
        </div>
      )}
      {/* 分析总结 */}
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{opinion.summary}</div>
    </div>
  );
}

/** 通用按钮样式 */
const btnStyle: React.CSSProperties = {
  background: '#6366f1', color: '#fff', border: 'none', borderRadius: 3,
  padding: '4px 12px', fontSize: 12, cursor: 'pointer',
};

/**
 * ExportBar — 报告导出按钮栏（MD/HTML/TXT）
 */
function ExportBar() {
  const handleExport = (format: 'md' | 'html' | 'txt') => {
    const a = document.createElement('a');
    a.href = `/api/export/latest?format=${format}`;
    a.download = `report.${format === 'md' ? 'md' : format === 'html' ? 'html' : 'txt'}`;
    a.click();
  };

  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 16, justifyContent: 'flex-end' }}>
      <span style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: '28px' }}>{t("report.export")}</span>
      <button onClick={() => handleExport('md')} style={btnStyle}>📄 Markdown</button>
      <button onClick={() => handleExport('html')} style={{ ...btnStyle, background: '#10b981' }}>🌐 HTML</button>
      <button onClick={() => handleExport('txt')} style={{ ...btnStyle, background: '#6b7280' }}>📝 纯文本</button>
    </div>
  );
}

/**
 * AgentRadarChart — 各分析师置信度 SVG 雷达图
 */
function AgentRadarChart({ opinions }: { opinions: any[] }) {
  if (!opinions || opinions.length < 2) return null;

  const cx = 130, cy = 130, r = 100;
  const n = opinions.length;
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (i: number, val: number) => {
    const angle = -Math.PI / 2 + i * angleStep;
    return { x: cx + val * r * Math.cos(angle), y: cy + val * r * Math.sin(angle) };
  };

  const points = opinions.map((op, i) => getPoint(i, op.confidence || 0));
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ') + ' Z';

  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: 12, minWidth: 280 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>{t("report.radar")}</div>
      <svg width={260} height={260} viewBox="0 0 260 260">
        {[0.25, 0.5, 0.75, 1].map((s) => (
          <circle key={s} cx={cx} cy={cy} r={r * s} fill="none" stroke="var(--border)" strokeWidth={0.5} />
        ))}
        {opinions.map((_, i) => {
          const p = getPoint(i, 1);
          return <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="var(--border)" strokeWidth={0.5} />;
        })}
        <path d={pathD} fill="#6366f144" stroke="#6366f1" strokeWidth={1.5} />
        {opinions.map((op, i) => {
          const p = getPoint(i, op.confidence || 0);
          const label = getPoint(i, 1.2);
          return (
            <g key={i}>
              <circle cx={p.x} cy={p.y} r={3} fill="#6366f1" />
              <text x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle" fontSize={10} fill="var(--text-muted)">
                {(op.agent_name || '').slice(0, 4)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

/**
 * StancePieChart — 各分析师立场分布 SVG 饼图
 */
function StancePieChart({ opinions }: { opinions: any[] }) {
  if (!opinions || opinions.length === 0) return null;

  const counts = { bullish: 0, bearish: 0, neutral: 0 };
  opinions.forEach((op) => {
    const s = op.stance || 'neutral';
    if (s.includes('bullish')) counts.bullish++;
    else if (s.includes('bearish')) counts.bearish++;
    else counts.neutral++;
  });

  const total = opinions.length;
  const colors = { bullish: '#10b981', bearish: '#ef4444', neutral: '#6b7280' };
  const labelKeys: Record<string, string> = { bullish: 'report.stance_bullish', bearish: 'report.stance_bearish', neutral: 'report.stance_neutral' };
  const cx = 90, cy = 90, r = 70;

  let startAngle = -Math.PI / 2;
  const segments = (Object.keys(counts) as Array<keyof typeof counts>).filter((k) => counts[k] > 0).map((k) => {
    const count = counts[k];
    const angle = (count / total) * 2 * Math.PI;
    const endAngle = startAngle + angle;
    const largeArc = angle > Math.PI ? 1 : 0;
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);
    const path = `M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${largeArc} 1 ${x2},${y2} Z`;
    const midAngle = startAngle + angle / 2;
    const labelPos = { x: cx + (r * 0.6) * Math.cos(midAngle), y: cy + (r * 0.6) * Math.sin(midAngle) };
    startAngle = endAngle;
    return { key: k, path, color: colors[k], count, labelPos, label: t(labelKeys[k]) || k };
  });

  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: 12, minWidth: 220 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>{t("report.pie")}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <svg width={180} height={180} viewBox="0 0 180 180">
          {segments.map((seg) => (
            <g key={seg.key}>
              <path d={seg.path} fill={seg.color} opacity={0.85} />
              <text x={seg.labelPos.x} y={seg.labelPos.y} textAnchor="middle" dominantBaseline="middle" fontSize={11} fill="#fff" fontWeight={600}>
                {seg.count}
              </text>
            </g>
          ))}
        </svg>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          {segments.map((seg) => (
            <div key={seg.key} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: seg.color, display: 'inline-block' }} />
              <span>{seg.label}: {seg.count} ({((seg.count / total) * 100).toFixed(0)}%)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
