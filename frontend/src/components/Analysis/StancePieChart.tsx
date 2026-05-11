import { memo } from 'react';
import { t } from '../../i18n';

const LABEL_KEYS: Record<string, string> = {
  bullish: 'report.stance_bullish',
  bearish: 'report.stance_bearish',
  neutral: 'report.stance_neutral',
};

const COLORS: Record<string, string> = {
  bullish: '#34C759',
  bearish: '#FF3B30',
  neutral: '#8e8e93',
};

const StancePieChart = memo(function StancePieChart({ opinions }: { opinions: any[] }) {
  if (!opinions || opinions.length === 0) return null;
  const counts = { bullish: 0, bearish: 0, neutral: 0 };
  opinions.forEach((op) => {
    const s = op.stance || 'neutral';
    if (s.includes('bullish')) counts.bullish++;
    else if (s.includes('bearish')) counts.bearish++;
    else counts.neutral++;
  });
  const total = opinions.length;
  const cx = 90, cy = 90, r = 70;
  let startAngle = -Math.PI / 2;
  const segments = (Object.keys(counts) as Array<keyof typeof counts>)
    .filter((k) => counts[k] > 0)
    .map((k) => {
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
      const labelPos = {
        x: cx + (r * 0.6) * Math.cos(midAngle),
        y: cy + (r * 0.6) * Math.sin(midAngle),
      };
      startAngle = endAngle;
      return { key: k, path, color: COLORS[k], count, labelPos, label: t(LABEL_KEYS[k]) || k };
    });

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12, padding: 14, minWidth: 220,
      backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
    }}>
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
              <span style={{ width: 10, height: 10, borderRadius: 3, background: seg.color, display: 'inline-block' }} />
              <span>{seg.label}: {seg.count} ({((seg.count / total) * 100).toFixed(0)}%)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}, (prev, next) => JSON.stringify(prev.opinions) === JSON.stringify(next.opinions));

export default StancePieChart;