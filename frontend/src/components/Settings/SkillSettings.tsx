// frontend/src/components/Settings/SkillSettings.tsx
// Skill 配置子面板 — 技能浏览（按类别分组）+ 增删改查 + SKILL.md 安装/卸载

import { useState, useEffect, useCallback, useRef } from 'react';
import { t } from '../../i18n';
import { getSkills, installSkillFromUrl, installSkillUpload, uninstallSkill } from '../../api/client';
import { CATEGORY_ICONS, CATEGORY_COLORS } from '../../constants/theme';
import type { SkillInfo } from '../../types';

/** 弹窗输入框样式 */
const modalInput: React.CSSProperties = {
  width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border-strong)',
  borderRadius: 6, padding: '7px 10px', color: 'var(--text)', fontSize: 13,
  outline: 'none', boxSizing: 'border-box',
};
const modalLabel: React.CSSProperties = {
  fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4, display: 'block',
};

const MARKET_OPTIONS = [
  { value: 'a_share', label: '🇨🇳 A股' },
  { value: 'h_stock', label: '🇭🇰 港股' },
  { value: 'us_stock', label: '🇺🇸 美股' },
];
const CATEGORY_OPTIONS = [
  'fundamental', 'technical', 'sentiment', 'news', 'macro',
  'data', 'sector', 'flow', 'analysis', 'trading', 'general',
];

export function SkillSettings() {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  // 编辑弹窗
  const [editSkill, setEditSkill] = useState<SkillInfo | null>(null);
  const [editDesc, setEditDesc] = useState('');
  const [editLabel, setEditLabel] = useState('');
  // 删除确认
  const [deleteTarget, setDeleteTarget] = useState<SkillInfo | null>(null);
  // 新建弹窗
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newLabel, setNewLabel] = useState('');
  const [newCategory, setNewCategory] = useState('general');
  const [newMarkets, setNewMarkets] = useState<string[]>(['a_share', 'h_stock', 'us_stock']);
  // 安装 SKILL.md
  const [showInstallUrl, setShowInstallUrl] = useState(false);
  const [installUrl, setInstallUrl] = useState('');
  const [installing, setInstalling] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSkills();
      setSkills(data || []);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleGroup = (cat: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  };

  // 按 category 分组
  const grouped = new Map<string, SkillInfo[]>();
  for (const sk of skills) {
    const cat = sk.category || 'general';
    if (!grouped.has(cat)) grouped.set(cat, []);
    grouped.get(cat)!.push(sk);
  }

  /** 判断技能来源标签 */
  const getSourceTag = (sk: SkillInfo): { icon: string; text: string; color: string } | null => {
    if (sk._source === 'skill_md') return { icon: '📥', text: t('settings.installed'), color: 'var(--accent-green)' };
    if (sk._custom) return { icon: '🏷️', text: t('settings.custom'), color: 'var(--accent-blue)' };
    return { icon: '🔒', text: t('settings.builtin'), color: 'var(--text-muted)' };
  };

  /** 判断是否可以卸载 */
  const canUninstall = (sk: SkillInfo) => sk._source === 'skill_md';

  /** 判断是否可编辑（自定义或 SKILL.md 安装的） */
  const canEdit = (sk: SkillInfo) => sk._custom || sk._source === 'skill_md';

  // ─── 编辑 ───
  const openEdit = (sk: SkillInfo) => {
    setEditSkill(sk);
    setEditDesc(sk.description);
    setEditLabel(sk.label || '');
  };
  const saveEdit = async () => {
    if (!editSkill) return;
    try {
      await fetch(`/api/skills/${editSkill.name}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: editDesc, label: editLabel }),
      });
      setEditSkill(null);
      load();
    } catch { /* silent */ }
  };

  // ─── 删除 ───
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await fetch(`/api/skills/${deleteTarget.name}`, { method: 'DELETE' });
      setDeleteTarget(null);
      load();
    } catch { /* silent */ }
  };

  // ─── 从 URL 安装 SKILL.md ───
  const handleInstallUrl = async () => {
    if (!installUrl.trim()) return;
    setInstalling(true);
    try {
      const res = await installSkillFromUrl(installUrl);
      if (res.error) { alert(res.error); return; }
      setShowInstallUrl(false);
      setInstallUrl('');
      load();
    } catch (e: any) { alert(e.message || '安装失败'); }
    setInstalling(false);
  };

  // ─── 上传文件安装 ───
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setInstalling(true);
    try {
      const res = await installSkillUpload(file);
      if (res.error) { alert(res.error); return; }
      load();
    } catch (err: any) { alert(err.message || '上传失败'); }
    setInstalling(false);
    e.target.value = '';
  };

  // ─── 卸载 SKILL.md 技能 ───
  const handleUninstall = async (name: string) => {
    if (!confirm(t('settings.uninstall_confirm') + `: ${name}?`)) return;
    try {
      await uninstallSkill(name);
      load();
    } catch { /* silent */ }
  };

  // ─── 新建 ───
  const handleCreate = async () => {
    if (!newName.trim() || !newDesc.trim()) return;
    try {
      await fetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newName, description: newDesc, label: newLabel,
          category: newCategory, markets: newMarkets,
        }),
      });
      setShowCreate(false);
      setNewName(''); setNewDesc(''); setNewLabel('');
      setNewCategory('general'); setNewMarkets(['a_share', 'h_stock', 'us_stock']);
      load();
    } catch { /* silent */ }
  };

  if (loading) {
    return <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t('history.loading')}</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* 操作按钮行 */}
      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end', marginBottom: 4 }}>
        <button
          onClick={() => setShowInstallUrl(true)}
          style={{
            background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 6, padding: '6px 12px', fontSize: 12,
            color: 'var(--text-secondary)', cursor: 'pointer',
          }}
        >📥 {t('settings.install_from_url')}</button>
        <label style={{
          background: 'var(--bg-input)', border: '1px solid var(--border)',
          borderRadius: 6, padding: '6px 12px', fontSize: 12,
          color: 'var(--text-secondary)', cursor: 'pointer', display: 'inline-flex', alignItems: 'center',
        }}>
          📤 {t('settings.install_upload')}
          <input ref={fileInputRef} type="file" accept=".md" onChange={handleFileUpload} style={{ display: 'none' }} />
        </label>
        <button
          onClick={() => setShowCreate(true)}
          style={{
            background: 'var(--accent-blue)', color: '#fff',
            border: 'none', borderRadius: 6, padding: '6px 14px', fontSize: 12,
            fontWeight: 600, cursor: 'pointer',
          }}
        >+ {t('settings.skill_create')}</button>
      </div>

      {skills.length === 0 && (
        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t('settings.no_skills')}</div>
      )}

      {Array.from(grouped.entries()).map(([cat, items]) => {
        const isCollapsed = collapsed.has(cat);
        const catIcon = CATEGORY_ICONS[cat] || '⚙️';
        const catColor = CATEGORY_COLORS[cat] || '#8e8e93';
        return (
          <div key={cat} style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 8, overflow: 'hidden',
          }}>
            {/* 类别头 */}
            <div
              onClick={() => toggleGroup(cat)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '8px 12px', cursor: 'pointer',
                background: 'var(--bg-input)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  width: 22, height: 22, borderRadius: 4,
                  background: catColor + '18', color: catColor,
                  fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>{catIcon}</span>
                <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)', textTransform: 'capitalize' }}>
                  {cat}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{items.length}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 12, transition: 'transform 0.2s', transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)' }}>
                  ▼
                </span>
              </div>
            </div>

            {/* 技能列表 */}
            {!isCollapsed && (
              <div style={{ padding: '6px 12px 10px' }}>
                {items.map((sk) => {
                  const sourceTag = getSourceTag(sk);
                  return (
                    <div key={sk.name} style={{
                      padding: '8px 0',
                      borderBottom: '1px solid var(--border)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)' }}>
                          {sk.label || sk.name}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                          {sk.name}
                        </span>
                        {/* 来源标签 */}
                        {sourceTag && (
                          <span style={{
                            fontSize: 10, color: sourceTag.color,
                            background: sourceTag.color + '18',
                            borderRadius: 3, padding: '1px 6px',
                            display: 'inline-flex', alignItems: 'center', gap: 3,
                          }}>
                            {sourceTag.icon} {sourceTag.text}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
                        {sk.description}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {(sk.markets || []).map((m) => {
                            const mo = MARKET_OPTIONS.find(o => o.value === m);
                            return (
                              <span key={m} style={{
                                fontSize: 10, color: 'var(--text-muted)',
                                background: 'var(--bg-input)', borderRadius: 3, padding: '1px 5px',
                              }}>
                                {mo ? mo.label : m}
                              </span>
                            );
                          })}
                        </div>
                        {/* 操作按钮 */}
                        <div style={{ display: 'flex', gap: 4 }}>
                          {canEdit(sk) && (
                            <button
                              onClick={() => openEdit(sk)}
                              style={{
                                background: 'none', border: 'none', color: 'var(--accent-blue)',
                                cursor: 'pointer', fontSize: 11, padding: '2px 4px',
                              }}
                            >✎ {t('settings.edit')}</button>
                          )}
                          {canUninstall(sk) && (
                            <button
                              onClick={() => handleUninstall(sk.name)}
                              style={{
                                background: 'none', border: 'none', color: 'var(--accent-red)',
                                cursor: 'pointer', fontSize: 11, padding: '2px 4px',
                              }}
                            >🗑 {t('settings.uninstall')}</button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      {/* ─── 编辑弹窗 ─── */}
      {editSkill && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setEditSkill(null)}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 10, padding: 20, width: 380,
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', marginBottom: 16 }}>
              {CATEGORY_ICONS[editSkill.category] || '⚙️'} {t('settings.edit_skill')}: {editSkill.name}
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_label')}</label>
              <input value={editLabel} onChange={(e) => setEditLabel(e.target.value)} style={modalInput} placeholder="中文短名称" />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_desc')}</label>
              <textarea
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                rows={3}
                style={{ ...modalInput, resize: 'vertical', fontSize: 12 }}
              />
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setEditSkill(null)} style={{
                background: 'none', border: '1px solid var(--border)', borderRadius: 6,
                padding: '6px 14px', fontSize: 12, color: 'var(--text-muted)', cursor: 'pointer',
              }}>{t('settings.cancel')}</button>
              <button onClick={saveEdit} style={{
                background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 6,
                padding: '6px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
              }}>{t('settings.save')}</button>
            </div>
          </div>
        </div>
      )}

      {/* ─── 删除确认弹窗 ─── */}
      {deleteTarget && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setDeleteTarget(null)}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 10, padding: 20, width: 340,
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent-red)', marginBottom: 12 }}>
              🗑 {t('settings.confirm_delete')}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
              {t('settings.delete_skill_confirm')}: <strong>{deleteTarget.label || deleteTarget.name}</strong>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setDeleteTarget(null)} style={{
                background: 'none', border: '1px solid var(--border)', borderRadius: 6,
                padding: '6px 14px', fontSize: 12, color: 'var(--text-muted)', cursor: 'pointer',
              }}>{t('settings.cancel')}</button>
              <button onClick={confirmDelete} style={{
                background: 'var(--accent-red)', color: '#fff', border: 'none', borderRadius: 6,
                padding: '6px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
              }}>{t('settings.delete')}</button>
            </div>
          </div>
        </div>
      )}

      {/* ─── 从 URL 安装弹窗 ─── */}
      {showInstallUrl && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => { setShowInstallUrl(false); setInstallUrl(''); }}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 10, padding: 20, width: 420,
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', marginBottom: 16 }}>
              📥 {t('settings.install_from_url')}
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_url_label')}</label>
              <input
                value={installUrl}
                onChange={(e) => setInstallUrl(e.target.value)}
                style={modalInput}
                placeholder={t('settings.install_url_placeholder')}
                autoFocus
                onKeyDown={(e) => { if (e.key === 'Enter') handleInstallUrl(); }}
              />
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 14 }}>
              {t('settings.install_url_hint')}
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => { setShowInstallUrl(false); setInstallUrl(''); }} style={{
                background: 'none', border: '1px solid var(--border)', borderRadius: 6,
                padding: '6px 14px', fontSize: 12, color: 'var(--text-muted)', cursor: 'pointer',
              }}>{t('settings.cancel')}</button>
              <button
                onClick={handleInstallUrl}
                disabled={installing || !installUrl.trim()}
                style={{
                  background: installing ? 'var(--text-muted)' : 'var(--accent-blue)',
                  color: '#fff', border: 'none', borderRadius: 6,
                  padding: '6px 14px', fontSize: 12, fontWeight: 600,
                  cursor: installing ? 'not-allowed' : 'pointer',
                }}
              >
                {installing ? t('settings.installing') : t('settings.install')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── 新建 Skill 弹窗 ─── */}
      {showCreate && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setShowCreate(false)}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 10, padding: 20, width: 420, maxHeight: '80vh', overflow: 'auto',
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', marginBottom: 16 }}>
              + {t('settings.skill_create')}
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_name')}</label>
              <input value={newName} onChange={(e) => setNewName(e.target.value)} style={modalInput} placeholder="custom_skill_name" />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_label')}</label>
              <input value={newLabel} onChange={(e) => setNewLabel(e.target.value)} style={modalInput} placeholder="中文短名称" />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_desc')}</label>
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                rows={3}
                style={{ ...modalInput, resize: 'vertical', fontSize: 12 }}
              />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_category')}</label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                style={modalInput}
              >
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>{CATEGORY_ICONS[c] || '⚙️'} {c}</option>
                ))}
              </select>
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.skill_markets')}</label>
              <div style={{ display: 'flex', gap: 6 }}>
                {MARKET_OPTIONS.map((mo) => {
                  const selected = newMarkets.includes(mo.value);
                  return (
                    <button
                      key={mo.value}
                      onClick={() => setNewMarkets(prev => selected ? prev.filter(m => m !== mo.value) : [...prev, mo.value])}
                      style={{
                        background: selected ? 'rgba(99,102,241,0.15)' : 'var(--bg-input)',
                        border: `1px solid ${selected ? 'var(--accent-blue)' : 'var(--border)'}`,
                        borderRadius: 4, padding: '4px 10px', fontSize: 12,
                        color: selected ? 'var(--accent-blue)' : 'var(--text-muted)',
                        cursor: 'pointer',
                      }}
                    >{mo.label}</button>
                  );
                })}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowCreate(false)} style={{
                background: 'none', border: '1px solid var(--border)', borderRadius: 6,
                padding: '6px 14px', fontSize: 12, color: 'var(--text-muted)', cursor: 'pointer',
              }}>{t('settings.cancel')}</button>
              <button onClick={handleCreate} style={{
                background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 6,
                padding: '6px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
              }}>{t('settings.create')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
