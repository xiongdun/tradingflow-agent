import { memo } from 'react';
import { t } from '../../i18n';

const AgentRadarChart = memo(function AgentRadarChart({ opinions }: { opinions: any[] }) {
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
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12, padding: 14, minWidth: 280,
      backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
    }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>{t("report.radar")}</div>
      <svg width={260} height={260} viewBox="0 0 260 260">
        {[0.25, 0.5, 0.75, 1].map((s) => (
          <circle key={s} cx={cx} cy={cy} r={r * s} fill="none" stroke="var(--border)" strokeWidth={0.5} />
        ))}
        {opinions.map((_, i) => {
          const p = getPoint(i, 1);
          return <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="var(--border)" strokeWidth={0.5} />;
        })}
        <path d={pathD} fill="rgba(0,122,255,0.15)" stroke="var(--accent-blue)" strokeWidth={1.5} />
        {opinions.map((op, i) => {
          const p = getPoint(i, op.confidence || 0);
          const label = getPoint(i, 1.2);
          return (
            <g key={i}>
              <circle cx={p.x} cy={p.y} r={3} fill="var(--accent-blue)" />
              <text x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle" fontSize={10} fill="var(--text-muted)">
                {(op.agent_name || '').slice(0, 4)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}, (prev, next) => JSON.stringify(prev.opinions) === JSON.stringify(next.opinions));

export default AgentRadarChart;