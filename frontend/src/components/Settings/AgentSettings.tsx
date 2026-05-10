// frontend/src/components/Settings/AgentSettings.tsx
// Agent 配置子面板 — Agent 列表浏览 + 技能管理 + 增删改查

import { useState, useEffect, useCallback } from 'react';
import { t } from '../../i18n';
import { getAgents, addAgentSkill, removeAgentSkill, resetAgentSkills, getSkills } from '../../api/client';
import type { AgentInfo, SkillInfo } from '../../types';

/** 各 Agent 角色对应图标 — 与 AgentNode / Sidebar 保持一致 */
const ROLE_ICONS: Record<string, string> = {
  fundamental: '📊', technical: '📈', sentiment: '🔥',
  news: '📰', macro: '🌐', hot_money: '💰',
  risk: '⚠️', summarizer: '✦', trading: '💹',
  sector_rotation: '🔄', quant: '🔬',
};

/** 各 Agent 角色对应颜色 — 与 theme.ts STANCE_COLORS 一致 */
const ROLE_COLORS: Record<string, string> = {
  fundamental: '#34C759', technical: '#007AFF', sentiment: '#FF9500',
  news: '#AF52DE', macro: '#5AC8FA', hot_money: '#FF3B30',
  risk: '#FFCC00', summarizer: '#AF52DE', trading: '#FF6B35',
  sector_rotation: '#FF2D55', quant: '#64D2FF',
};

/** 弹窗输入框样式 */
const modalInput: React.CSSProperties = {
  width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border-strong)',
  borderRadius: 6, padding: '7px 10px', color: 'var(--text)', fontSize: 13,
  outline: 'none', boxSizing: 'border-box',
};
const modalLabel: React.CSSProperties = {
  fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4, display: 'block',
};

export function AgentSettings() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [allSkills, setAllSkills] = useState<SkillInfo[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  // 编辑弹窗状态
  const [editAgent, setEditAgent] = useState<AgentInfo | null>(null);
  const [editName, setEditName] = useState('');
  const [editPrompt, setEditPrompt] = useState('');
  // 删除确认状态
  const [deleteTarget, setDeleteTarget] = useState<AgentInfo | null>(null);
  // 新建弹窗状态
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('');
  const [newPrompt, setNewPrompt] = useState('');
  const [newSkills, setNewSkills] = useState<string[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [a, s] = await Promise.all([getAgents(), getSkills()]);
      setAgents(a || []);
      setAllSkills(s || []);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  // ─── 技能管理 ───
  const handleAddSkill = async (role: string, skill: string) => {
    await addAgentSkill(role, skill);
    load();
  };
  const handleRemoveSkill = async (role: string, skill: string) => {
    await removeAgentSkill(role, skill);
    load();
  };
  const handleReset = async (role: string) => {
    await resetAgentSkills(role);
    load();
  };

  // ─── 编辑 Agent ───
  const openEdit = (agent: AgentInfo) => {
    setEditAgent(agent);
    setEditName(agent.name);
    setEditPrompt('');
  };
  const saveEdit = async () => {
    if (!editAgent) return;
    try {
      await fetch(`/api/agents/${editAgent.role}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName, extra_prompt: editPrompt }),
      });
      setEditAgent(null);
      load();
    } catch { /* silent */ }
  };

  // ─── 删除 Agent ───
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await fetch(`/api/agents/${deleteTarget.role}`, { method: 'DELETE' });
      setDeleteTarget(null);
      load();
    } catch { /* silent */ }
  };

  // ─── 新建 Agent ───
  const handleCreate = async () => {
    if (!newName.trim() || !newRole.trim()) return;
    try {
      await fetch('/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName, role: newRole, extra_prompt: newPrompt, default_skills: newSkills }),
      });
      setShowCreate(false);
      setNewName(''); setNewRole(''); setNewPrompt(''); setNewSkills([]);
      load();
    } catch { /* silent */ }
  };

  if (loading) {
    return <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t('history.loading')}</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* 新建按钮 */}
      <button
        onClick={() => setShowCreate(true)}
        style={{
          alignSelf: 'flex-end', background: 'var(--accent-blue)', color: '#fff',
          border: 'none', borderRadius: 6, padding: '6px 14px', fontSize: 12,
          fontWeight: 600, cursor: 'pointer', marginBottom: 4,
        }}
      >+ {t('settings.agent_create')}</button>

      {agents.length === 0 && (
        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t('settings.no_agents')}</div>
      )}

      {agents.map((agent) => {
        const isOpen = expanded === agent.role;
        const current = new Set(agent.current_skills || []);
        const icon = ROLE_ICONS[agent.role] || '🧠';
        const color = ROLE_COLORS[agent.role] || '#8e8e93';
        const isCustom = agent.role.startsWith('custom_');

        return (
          <div key={agent.role} style={{
            background: 'var(--bg-card)', border: `1px solid ${isOpen ? color + '40' : 'var(--border)'}`,
            borderRadius: 8, overflow: 'hidden', transition: 'border-color 0.2s',
          }}>
            {/* Agent 头部 */}
            <div
              onClick={() => setExpanded(isOpen ? null : agent.role)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 12px', cursor: 'pointer',
                background: isOpen ? color + '08' : 'transparent',
                transition: 'background 0.2s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  width: 28, height: 28, borderRadius: 6,
                  background: color + '18', color, fontSize: 15,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>{icon}</span>
                <div>
                  <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)' }}>{agent.name}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8, fontFamily: 'monospace' }}>{agent.role}</span>
                  {isCustom && (
                    <span style={{
                      fontSize: 10, color: 'var(--accent-blue)', background: 'rgba(99,102,241,0.1)',
                      borderRadius: 3, padding: '1px 5px', marginLeft: 6,
                    }}>自定义</span>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  fontSize: 11, color,
                  background: color + '14', borderRadius: 4, padding: '2px 6px',
                }}>
                  {current.size} {t('settings.skill_count')}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: 12, transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'none' }}>
                  ▼
                </span>
              </div>
            </div>

            {/* 技能列表 + 操作按钮（展开时） */}
            {isOpen && (
              <div style={{ padding: '8px 12px 12px', borderTop: '1px solid var(--border)' }}>
                {/* 已有技能 */}
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600 }}>
                  {t('settings.current_skills')}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
                  {(agent.current_skills || []).map((sk) => (
                    <span key={sk} style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      background: color + '14', color,
                      borderRadius: 4, padding: '3px 8px', fontSize: 11, fontWeight: 600,
                    }}>
                      {sk}
                      <button
                        onClick={(e) => { e.stopPropagation(); handleRemoveSkill(agent.role, sk); }}
                        style={{
                          background: 'none', border: 'none', color: 'var(--accent-red)',
                          cursor: 'pointer', fontSize: 12, padding: 0, lineHeight: 1,
                        }}
                      >×</button>
                    </span>
                  ))}
                  {current.size === 0 && (
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      {t('settings.no_skills_assigned')}
                    </span>
                  )}
                </div>

                {/* 可添加的技能 */}
                {(agent.available_skills || []).filter((s) => !current.has(s)).length > 0 && (
                  <>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600 }}>
                      {t('settings.available_skills')}
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                      {(agent.available_skills || []).filter((s) => !current.has(s)).map((sk) => (
                        <button
                          key={sk}
                          onClick={() => handleAddSkill(agent.role, sk)}
                          style={{
                            background: 'var(--bg-input)', border: '1px dashed var(--border)',
                            borderRadius: 4, padding: '3px 8px', fontSize: 11,
                            color: 'var(--text-muted)', cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                        >+ {sk}</button>
                      ))}
                    </div>
                  </>
                )}

                {/* 操作按钮行 */}
                <div style={{ display: 'flex', gap: 6, marginTop: 4, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                  <button
                    onClick={() => handleReset(agent.role)}
                    style={{
                      background: 'none', border: '1px solid var(--border)',
                      borderRadius: 4, padding: '3px 10px', fontSize: 11,
                      color: 'var(--text-muted)', cursor: 'pointer',
                    }}
                  >↺ {t('settings.reset_skills')}</button>
                  <button
                    onClick={(e) => { e.stopPropagation(); openEdit(agent); }}
                    style={{
                      background: 'none', border: '1px solid var(--border)',
                      borderRadius: 4, padding: '3px 10px', fontSize: 11,
                      color: 'var(--accent-blue)', cursor: 'pointer',
                    }}
                  >✎ {t('settings.edit')}</button>
                  {isCustom && (
                    <button
                      onClick={(e) => { e.stopPropagation(); setDeleteTarget(agent); }}
                      style={{
                        background: 'none', border: '1px solid var(--accent-red)',
                        borderRadius: 4, padding: '3px 10px', fontSize: 11,
                        color: 'var(--accent-red)', cursor: 'pointer',
                      }}
                    >🗑 {t('settings.delete')}</button>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* ─── 编辑弹窗 ─── */}
      {editAgent && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setEditAgent(null)}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 10, padding: 20, width: 380, maxHeight: '80vh', overflow: 'auto',
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', marginBottom: 16 }}>
              {ROLE_ICONS[editAgent.role] || '🧠'} {t('settings.edit_agent')}: {editAgent.name}
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.agent_name')}</label>
              <input value={editName} onChange={(e) => setEditName(e.target.value)} style={modalInput} />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.agent_extra_prompt')}</label>
              <textarea
                value={editPrompt}
                onChange={(e) => setEditPrompt(e.target.value)}
                placeholder={t('settings.agent_extra_prompt_hint')}
                rows={4}
                style={{ ...modalInput, resize: 'vertical', fontFamily: 'monospace', fontSize: 12 }}
              />
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setEditAgent(null)} style={{
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
              {t('settings.delete_agent_confirm')}: <strong>{deleteTarget.name}</strong> ({deleteTarget.role})
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

      {/* ─── 新建 Agent 弹窗 ─── */}
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
              + {t('settings.agent_create')}
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.agent_name')}</label>
              <input value={newName} onChange={(e) => setNewName(e.target.value)} style={modalInput} placeholder="自定义分析师" />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.agent_role')}</label>
              <input value={newRole} onChange={(e) => setNewRole(e.target.value)} style={modalInput} placeholder="custom_analyst" />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{t('settings.agent_role_hint')}</div>
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.agent_extra_prompt')}</label>
              <textarea
                value={newPrompt}
                onChange={(e) => setNewPrompt(e.target.value)}
                placeholder={t('settings.agent_extra_prompt_hint')}
                rows={3}
                style={{ ...modalInput, resize: 'vertical', fontFamily: 'monospace', fontSize: 12 }}
              />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={modalLabel}>{t('settings.default_skills')}</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {allSkills.map((sk) => {
                  const selected = newSkills.includes(sk.name);
                  return (
                    <button
                      key={sk.name}
                      onClick={() => setNewSkills(prev => selected ? prev.filter(s => s !== sk.name) : [...prev, sk.name])}
                      style={{
                        background: selected ? 'rgba(99,102,241,0.15)' : 'var(--bg-input)',
                        border: `1px solid ${selected ? 'var(--accent-blue)' : 'var(--border)'}`,
                        borderRadius: 4, padding: '3px 8px', fontSize: 11,
                        color: selected ? 'var(--accent-blue)' : 'var(--text-muted)',
                        cursor: 'pointer', fontWeight: selected ? 600 : 400,
                      }}
                    >{selected ? '✓ ' : ''}{sk.label || sk.name}</button>
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
