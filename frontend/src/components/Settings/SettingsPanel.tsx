// frontend/src/components/Settings/SettingsPanel.tsx
// 系统设置主容器 — 横排子 Tab 导航（与历史记录样式一致）+ 配置保存

import { useState, useEffect, useCallback, useRef } from 'react';
import { t } from '../../i18n';
import { getConfig, updateConfigBatch } from '../../api/client';
import { GeneralSettings } from './GeneralSettings';
import { LLMSettings } from './LLMSettings';
import { AgentSettings } from './AgentSettings';
import { SkillSettings } from './SkillSettings';

type SettingsTab = 'general' | 'llm' | 'agent' | 'skill';

const TABS: { key: SettingsTab; icon: string; labelKey: string }[] = [
  { key: 'general', icon: '⚙️', labelKey: 'settings.general' },
  { key: 'llm', icon: '🧠', labelKey: 'settings.llm' },
  { key: 'agent', icon: '🤖', labelKey: 'settings.agent' },
  { key: 'skill', icon: '🧩', labelKey: 'settings.skill' },
];

export function SettingsPanel() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');
  const [config, setConfig] = useState<Record<string, string>>({});
  const [initialConfig, setInitialConfig] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout>>();

  /** 加载配置 */
  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getConfig();
      const strConfig: Record<string, string> = {};
      for (const [k, v] of Object.entries(data || {})) {
        strConfig[k] = String(v ?? '');
      }
      setConfig(strConfig);
      setInitialConfig(strConfig);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => { loadConfig(); }, [loadConfig]);

  /** 配置变更 */
  const handleChange = (key: string, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  /** 是否有未保存的变更 */
  const isDirty = JSON.stringify(config) !== JSON.stringify(initialConfig);

  /** 保存配置 */
  const handleSave = async () => {
    setSaving(true);
    try {
      const updates: Record<string, string> = {};
      for (const [k, v] of Object.entries(config)) {
        if (v !== initialConfig[k]) {
          updates[k] = v;
        }
      }
      if (Object.keys(updates).length > 0) {
        await updateConfigBatch(updates);
      }
      setInitialConfig({ ...config });
      setSaved(true);
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => setSaved(false), 3000);
    } catch { /* silent */ }
    setSaving(false);
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
        {t('history.loading')}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg)' }}>
      {/* 横排子 Tab 栏 — 与历史记录 HistoryPanel 样式一致 */}
      <div style={{
        display: 'flex', gap: 8, padding: '8px 16px',
        borderBottom: '1px solid var(--border)', background: 'var(--bg-panel)',
        alignItems: 'center',
      }}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '4px 16px', fontSize: 12, fontWeight: 600,
              background: activeTab === tab.key ? 'var(--bg-input)' : 'transparent',
              color: activeTab === tab.key ? 'var(--text)' : 'var(--text-muted)',
              border: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #6366f1' : '2px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ marginRight: 4 }}>{tab.icon}</span>
            {t(tab.labelKey)}
          </button>
        ))}

        {/* 右侧：保存状态 + 保存按钮 */}
        <div style={{ flex: 1 }} />
        {isDirty && (
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {t('settings.unsaved')}
          </span>
        )}
        {saved && (
          <span style={{ fontSize: 12, color: 'var(--accent-green)' }}>
            {t('settings.saved')}
          </span>
        )}
        {(activeTab === 'general' || activeTab === 'llm') && (
          <button
            onClick={handleSave}
            disabled={saving || !isDirty}
            style={{
              background: isDirty ? '#6366f1' : 'var(--bg-input)',
              color: isDirty ? '#fff' : 'var(--text-muted)',
              border: 'none', borderRadius: 4,
              padding: '3px 12px', fontSize: 12, fontWeight: 600,
              cursor: isDirty ? 'pointer' : 'default',
              opacity: saving || !isDirty ? 0.6 : 1,
              transition: 'all 0.2s',
            }}
          >
            {saving ? t('settings.saving') : t('settings.save')}
          </button>
        )}
      </div>

      {/* 内容区域 */}
      <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
        {activeTab === 'general' && <GeneralSettings config={config} onChange={handleChange} />}
        {activeTab === 'llm' && <LLMSettings config={config} onChange={handleChange} />}
        {activeTab === 'agent' && <AgentSettings />}
        {activeTab === 'skill' && <SkillSettings />}
      </div>
    </div>
  );
}
