// frontend/src/components/Settings/GeneralSettings.tsx
// 基础配置子面板 — 默认市场、超时、颜色方案、语言、日志级别

import { t } from '../../i18n';

interface Props {
  config: Record<string, string>;
  onChange: (key: string, value: string) => void;
}

const inputStyle: React.CSSProperties = {
  width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border-strong)',
  borderRadius: 6, padding: '7px 10px', color: 'var(--text)', fontSize: 13,
  outline: 'none', transition: 'border-color 0.2s', boxSizing: 'border-box',
};
const labelStyle: React.CSSProperties = {
  fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4,
};
const rowStyle: React.CSSProperties = {
  marginBottom: 16,
};

export function GeneralSettings({ config, onChange }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {/* 默认市场 */}
      <div style={rowStyle}>
        <div style={labelStyle}>📊 {t('settings.default_market')}</div>
        <select
          value={config.default_market || 'a_share'}
          onChange={(e) => onChange('default_market', e.target.value)}
          style={inputStyle}
        >
          <option value="a_share">{t('market.a_share')}</option>
          <option value="h_stock">{t('market.h_stock')}</option>
          <option value="us_stock">{t('market.us_stock')}</option>
        </select>
      </div>

      {/* 分析超时 */}
      <div style={rowStyle}>
        <div style={labelStyle}>⏱️ {t('settings.analysis_timeout')}</div>
        <input
          type="number"
          min={30}
          max={600}
          value={config.analysis_timeout || '120'}
          onChange={(e) => onChange('analysis_timeout', e.target.value)}
          style={inputStyle}
        />
      </div>

      {/* 涨跌颜色 */}
      <div style={rowStyle}>
        <div style={labelStyle}>🎨 {t('settings.color_scheme')}</div>
        <select
          value={config.color_scheme || 'cn'}
          onChange={(e) => onChange('color_scheme', e.target.value)}
          style={inputStyle}
        >
          <option value="cn">{t('settings.color_cn')}</option>
          <option value="international">{t('settings.color_intl')}</option>
        </select>
      </div>

      {/* 界面语言 */}
      <div style={rowStyle}>
        <div style={labelStyle}>🌐 {t('settings.language')}</div>
        <select
          value={config.language || 'zh'}
          onChange={(e) => onChange('language', e.target.value)}
          style={inputStyle}
        >
          <option value="zh">{t('settings.lang_zh')}</option>
          <option value="en">{t('settings.lang_en')}</option>
        </select>
      </div>

      {/* 日志级别 */}
      <div style={rowStyle}>
        <div style={labelStyle}>📋 {t('settings.log_level')}</div>
        <select
          value={config.log_level || 'INFO'}
          onChange={(e) => onChange('log_level', e.target.value)}
          style={inputStyle}
        >
          <option value="DEBUG">DEBUG</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
      </div>
    </div>
  );
}
