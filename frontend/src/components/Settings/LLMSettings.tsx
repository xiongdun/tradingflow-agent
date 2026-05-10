// frontend/src/components/Settings/LLMSettings.tsx
// 大模型配置子面板 — 供应商、模型、API Key、Base URL、温度、Max Tokens

import { useState } from 'react';
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

const PROVIDERS = [
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'qwen', label: '通义千问 (Qwen)' },
  { value: 'claude', label: 'Claude' },
  { value: 'ollama', label: 'Ollama (本地)' },
];

export function LLMSettings({ config, onChange }: Props) {
  const [showKey, setShowKey] = useState(false);
  const temp = parseFloat(config.llm_temperature || '0.3');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {/* LLM 供应商 */}
      <div style={rowStyle}>
        <div style={labelStyle}>🏢 {t('settings.llm_provider')}</div>
        <select
          value={config.llm_provider || 'deepseek'}
          onChange={(e) => onChange('llm_provider', e.target.value)}
          style={inputStyle}
        >
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
      </div>

      {/* 模型名称 */}
      <div style={rowStyle}>
        <div style={labelStyle}>📦 {t('settings.llm_model')}</div>
        <input
          type="text"
          value={config.llm_model || ''}
          onChange={(e) => onChange('llm_model', e.target.value)}
          placeholder="deepseek-chat"
          style={inputStyle}
        />
      </div>

      {/* API Key */}
      <div style={rowStyle}>
        <div style={labelStyle}>🔑 {t('settings.llm_api_key')}</div>
        <div style={{ position: 'relative' }}>
          <input
            type={showKey ? 'text' : 'password'}
            value={config.llm_api_key || ''}
            onChange={(e) => onChange('llm_api_key', e.target.value)}
            placeholder="sk-..."
            style={{ ...inputStyle, paddingRight: 70 }}
          />
          <button
            onClick={() => setShowKey(!showKey)}
            style={{
              position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', color: 'var(--text-muted)',
              fontSize: 11, cursor: 'pointer', padding: '2px 6px',
            }}
          >
            {showKey ? t('settings.hide_key') : t('settings.show_key')}
          </button>
        </div>
      </div>

      {/* API Base URL */}
      <div style={rowStyle}>
        <div style={labelStyle}>🌐 {t('settings.llm_base_url')}</div>
        <input
          type="text"
          value={config.llm_base_url || ''}
          onChange={(e) => onChange('llm_base_url', e.target.value)}
          placeholder="https://api.deepseek.com/v1"
          style={inputStyle}
        />
      </div>

      {/* 温度滑块 */}
      <div style={rowStyle}>
        <div style={{ ...labelStyle, display: 'flex', justifyContent: 'space-between' }}>
          <span>🌡️ {t('settings.llm_temperature')}</span>
          <span style={{ color: 'var(--accent-blue)', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
            {temp.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={temp}
          onChange={(e) => onChange('llm_temperature', e.target.value)}
          style={{ width: '100%', accentColor: 'var(--accent-blue)' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)' }}>
          <span>0 (确定性)</span>
          <span>1 (创造性)</span>
        </div>
      </div>

      {/* 最大 Token */}
      <div style={rowStyle}>
        <div style={labelStyle}>🔢 {t('settings.llm_max_tokens')}</div>
        <input
          type="number"
          min={256}
          max={32768}
          step={256}
          value={config.llm_max_tokens || '4096'}
          onChange={(e) => onChange('llm_max_tokens', e.target.value)}
          style={inputStyle}
        />
      </div>
    </div>
  );
}
