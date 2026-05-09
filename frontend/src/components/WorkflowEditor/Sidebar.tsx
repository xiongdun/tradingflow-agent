// frontend/src/components/WorkflowEditor/Sidebar.tsx
// 左侧边栏 — 分类折叠面板：输入节点、参数配置、分析师、技能、总结研判、预置模板

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useWorkflowStore } from '../../store/workflowStore';
import { getAgents, getSkills, getAdapterTypes } from '../../api/client';
import { t } from '../../i18n';
import { STANCE_COLORS, NODE_TYPE_COLORS, CATEGORY_COLORS, CATEGORY_ICONS } from '../../constants/theme';
import type { SkillInfo, AdapterTypeInfo } from '../../types';

/** 技能类别中文名（icon/color 从共享 theme.ts 导入，避免重复定义） */
const CATEGORY_LABELS: Record<string, string> = {
  fundamental: '基本面', technical: '技术面', sentiment: '情绪面',
  news: '新闻面', macro: '宏观面', data: '数据',
  sector: '板块', flow: '资金流', analysis: '分析',
  trading: '交易', general: '通用',
};

export function Sidebar() {
  const agents = useWorkflowStore((s) => s.agents);
  const setAgents = useWorkflowStore((s) => s.setAgents);
  const skills = useWorkflowStore((s) => s.skills);
  const setSkills = useWorkflowStore((s) => s.setSkills);
  const nodes = useWorkflowStore((s) => s.nodes);
  const addNode = useWorkflowStore((s) => s.addNode);
  const saveWorkflow = useWorkflowStore((s) => s.saveWorkflow);
  const exportWorkflow = useWorkflowStore((s) => s.exportWorkflow);
  const [showCustom, setShowCustom] = useState(false);
  const [customName, setCustomName] = useState('');
  const [showSave, setShowSave] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    input: true, config: true, agents: true, skills: false, adapters: true, events: true, summarizer: true, templates: true,
  });
  const [adapterTypes, setAdapterTypes] = useState<AdapterTypeInfo[]>([]);

  // 搜索防抖：200ms 延迟更新
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 200);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // 搜索过滤：匹配名称、描述、角色
  const q = debouncedQuery.trim().toLowerCase();
  const matchAgent = (a: any) => !q || a.name.toLowerCase().includes(q) || a.role.toLowerCase().includes(q);
  const matchSkill = (s: any) => !q || s.name.toLowerCase().includes(q) || (s.label || '').toLowerCase().includes(q) || (s.description || '').toLowerCase().includes(q) || s.category.toLowerCase().includes(q);

  useEffect(() => {
    getAgents().then(setAgents).catch(console.error);
    getSkills().then(setSkills).catch(console.error);
    getAdapterTypes().then(setAdapterTypes).catch(console.error);
  }, [setAgents, setSkills]);

  const toggle = (section: string) => setOpenSections((s) => ({ ...s, [section]: !s[section] }));

  const onDragStart = (e: React.DragEvent, data: string) => {
    e.dataTransfer.setData('application/reactflow', data);
    e.dataTransfer.effectAllowed = 'move';
  };

  /** 添加输入节点（只允许一个） */
  const addInputNode = () => {
    if (nodes.some((n) => n.type === 'input')) return;
    addNode({
      id: 'input', type: 'input',
      position: { x: 20, y: 120 },
      data: { label: '输入', symbol: '', market: 'a_share' },
    });
  };

  /** 添加配置节点（只允许一个） */
  const addConfigNode = () => {
    if (nodes.some((n) => n.type === 'config')) return;
    addNode({
      id: 'config', type: 'config',
      position: { x: 20, y: 300 },
      data: { label: '参数配置', period: 'daily', days: 120 },
    });
  };

  /** 添加分析师到画布（点击时同时创建关联 Skill 节点和连线） */
  const addAgentToCanvas = (role: string) => {
    if (nodes.some((n) => n.id === role)) return;
    const agent = agents.find((a) => a.role === role);
    const agentSkills = agent?.current_skills || [];
    const isTrading = role === 'trading';
    // 交易节点放在总结节点右侧，其他分析师竖排在中间
    const count = nodes.filter((n) => n.type === 'analyst').length;
    const pos = isTrading
      ? { x: 1120, y: 60 + Math.max(count - 1, 0) * 140 }
      : { x: 420, y: 60 + count * 140 };

    const batchNodes: any[] = [];
    const batchEdges: { id: string; source: string; target: string; sourceHandle: string; targetHandle: string }[] = [];

    // Analyst 或 Trading 节点
    batchNodes.push({
      id: role, type: isTrading ? 'trading' : 'analyst', position: pos,
      data: { role, label: agent?.name || role, skills: agentSkills },
    });

    // Skill 节点（垂直居中排列在 Analyst 左侧）
    const skillGap = 64;
    const startY = pos.y - ((agentSkills.length - 1) * skillGap) / 2;
    agentSkills.forEach((skName, i) => {
      const nodeId = `skill_${skName}`;
      if (!nodes.some((n) => n.id === nodeId)) {
        const skMeta = skills.find((s) => s.name === skName);
        batchNodes.push({
          id: nodeId, type: 'skill',
          position: { x: pos.x - 200, y: startY + i * skillGap },
          data: {
            skillName: skName, label: skMeta?.label || skName,
            category: skMeta?.category || 'general',
            description: skMeta?.description || skName,
            params: {},
          },
        });
      }
      batchEdges.push({
        id: `${nodeId}-${role}`, source: nodeId, target: role,
        sourceHandle: 'right', targetHandle: 'left',
      });
    });

    useWorkflowStore.setState((s) => ({
      nodes: [...s.nodes, ...batchNodes],
      edges: [...s.edges, ...batchEdges],
    }));
  };

  /** 添加技能到画布 */
  const addSkillToCanvas = (skill: SkillInfo) => {
    if (nodes.some((n) => n.id === skill.name)) return;
    const count = nodes.filter((n) => n.type === 'skill').length;
    addNode({
      id: skill.name, type: 'skill',
      position: { x: 320, y: 300 + count * 100 },
      data: { skillName: skill.name, label: skill.label || skill.name, category: skill.category, description: skill.description, params: skill.params || {} },
    });
  };

  /** 添加总结研判 */
  const addSummarizer = () => {
    if (nodes.some((n) => n.type === 'summarizer')) return;
    addNode({
      id: 'summarizer', type: 'summarizer',
      position: { x: 620, y: 120 },
      data: { role: 'summarizer', label: '总结研判', skills: [] },
    });
  };

  /** 添加自定义分析师 */
  const addCustomAgent = () => {
    const name = customName.trim();
    if (!name) return;
    const existing = nodes.filter((n) => n.id.startsWith('custom_')).length;
    const id = `custom_${existing + 1}`;
    const count = nodes.filter((n) => n.type === 'analyst').length;
    addNode({
      id, type: 'analyst',
      position: { x: 320, y: 60 + count * 120 },
      data: { role: id, label: name, skills: ['stock_info', 'kline_data'], isCustom: true },
    });
    setCustomName('');
    setShowCustom(false);
  };

  const handleSave = useCallback(async () => {
    if (!saveName.trim()) return;
    try {
      await saveWorkflow(saveName.trim());
      setShowSave(false);
      setSaveName('');
      alert(t("sidebar.saved"));
    } catch {
      alert(t("sidebar.save_failed"));
    }
  }, [saveName, saveWorkflow]);

  const refreshTemplates = useCallback(() => {
    fetch('/api/workflows').then((r) => r.json()).then(useWorkflowStore.getState().setWorkflows).catch(console.error);
  }, []);

  // 按类别分组技能（memoized）
  const skillsByCategory = useMemo(() => {
    const grouped: Record<string, SkillInfo[]> = {};
    skills.forEach((s) => {
      if (!grouped[s.category]) grouped[s.category] = [];
      grouped[s.category].push(s);
    });
    return grouped;
  }, [skills]);

  const SectionHeader = ({ section, label, icon }: { section: string; label: string; icon: string }) => (
    <div
      onClick={() => toggle(section)}
      style={{
        display: 'flex', alignItems: 'center', gap: 6, padding: '6px 0',
        cursor: 'pointer', userSelect: 'none',
      }}
    >
      <span style={{ fontSize: 10, color: 'var(--text-muted)', transition: 'transform 0.2s', transform: openSections[section] ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
      <span style={{ fontSize: 11 }}>{icon}</span>
      <span style={{ color: 'var(--text-muted)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5, flex: 1 }}>{label}</span>
    </div>
  );

  return (
    <div style={{
      width: '100%', height: '100%', background: 'var(--bg-panel)', borderRight: '1px solid var(--border)',
      padding: 12, overflowY: 'auto', boxSizing: 'border-box',
      backdropFilter: 'var(--blur)', WebkitBackdropFilter: 'var(--blur)',
    }}>
      {/* ── 搜索框 ── */}
      <div style={{ position: 'relative', marginBottom: 10 }}>
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="🔍 搜索节点、技能..."
          style={{
            width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border-strong)',
            borderRadius: 8, padding: '6px 10px 6px 28px', color: 'var(--text)', fontSize: 12,
            outline: 'none', boxSizing: 'border-box',
          }}
        />
        <span style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', fontSize: 11, color: 'var(--text-muted)' }}>🔍</span>
        {searchQuery && (
          <span
            onClick={() => setSearchQuery('')}
            style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', fontSize: 11, color: 'var(--text-muted)', cursor: 'pointer' }}
          >✕</span>
        )}
      </div>

      {/* ── 输入节点 ── */}
      <SectionHeader section="input" label="输入" icon="◆" />
      {openSections.input && (
        <div
          draggable
          onDragStart={(e) => onDragStart(e, 'input:input:输入')}
          onClick={addInputNode}
          style={{
            background: nodes.some((n) => n.type === 'input') ? 'var(--bg-input)' : 'var(--bg-card)',
            border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', marginBottom: 6,
            cursor: nodes.some((n) => n.type === 'input') ? 'default' : 'grab',
            opacity: nodes.some((n) => n.type === 'input') ? 0.4 : 1,
            fontSize: 12, color: 'var(--accent-green)', fontWeight: 500,
          }}
        >
          ◆ 股票代码 + 市场
        </div>
      )}

      {/* ── 参数配置 ── */}
      <SectionHeader section="config" label="参数配置" icon="⚙" />
      {openSections.config && (
        <div
          draggable
          onDragStart={(e) => onDragStart(e, 'config:config:参数配置')}
          onClick={addConfigNode}
          style={{
            background: nodes.some((n) => n.type === 'config') ? 'var(--bg-input)' : 'var(--bg-card)',
            border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', marginBottom: 6,
            cursor: nodes.some((n) => n.type === 'config') ? 'default' : 'grab',
            opacity: nodes.some((n) => n.type === 'config') ? 0.4 : 1,
            fontSize: 12, color: 'var(--accent-orange)', fontWeight: 500,
          }}
        >
          ⚙ K线周期 + 历史天数
        </div>
      )}

      {/* ── 分析师 ── */}
      <SectionHeader section="agents" label="分析师 Agent" icon="🤖" />
      {openSections.agents && (
        <>
          {agents.filter(matchAgent).map((agent) => {
            const color = STANCE_COLORS[agent.role] || '#8e8e93';
            const added = nodes.some((n) => n.id === agent.role);
            return (
              <div
                key={agent.role}
                draggable={!added}
                onDragStart={(e) => onDragStart(e, `analyst:${agent.role}:${agent.name}`)}
                onClick={() => addAgentToCanvas(agent.role)}
                style={{
                  background: added ? 'var(--bg-input)' : 'var(--bg-card)',
                  border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', marginBottom: 4,
                  cursor: added ? 'default' : 'grab', opacity: added ? 0.4 : 1,
                  backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                  <span style={{ color: 'var(--text)', fontSize: 12, fontWeight: 600 }}>{agent.name}</span>
                </div>
              </div>
            );
          })}

          {/* 自定义分析师 */}
          {showCustom ? (
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 10, padding: '8px 12px', marginBottom: 4,
            }}>
              <input
                autoFocus value={customName} onChange={(e) => setCustomName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustomAgent()}
                placeholder={t("sidebar.input_name")}
                style={{ width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8, padding: '5px 8px', color: 'var(--text)', fontSize: 12, marginBottom: 6 }}
              />
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={addCustomAgent} disabled={!customName.trim()} style={{ flex: 1, background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 8, padding: '4px 0', fontSize: 11, fontWeight: 600, opacity: customName.trim() ? 1 : 0.5 }}>{t("sidebar.add")}</button>
                <button onClick={() => { setShowCustom(false); setCustomName(''); }} style={{ flex: 1, background: 'var(--bg-input)', color: 'var(--text-muted)', border: '1px solid var(--border)', borderRadius: 8, padding: '4px 0', fontSize: 11 }}>{t("sidebar.cancel")}</button>
              </div>
            </div>
          ) : (
            <div onClick={() => setShowCustom(true)} style={{
              background: 'var(--bg-card)', border: '1px dashed var(--border-strong)', borderRadius: 10,
              padding: '6px 12px', marginBottom: 4, cursor: 'pointer', textAlign: 'center',
              color: 'var(--text-muted)', fontSize: 11,
            }}>+ {t("sidebar.custom_agent")}</div>
          )}
        </>
      )}

      {/* ── 技能节点 ── */}
      <SectionHeader section="skills" label="技能 Skill" icon="🧩" />
      {openSections.skills && Object.entries(skillsByCategory).filter(([_, catSkills]) => catSkills.some(matchSkill)).map(([cat, catSkills]) => {
        const label = CATEGORY_LABELS[cat] || CATEGORY_LABELS.general;
        return (
          <div key={cat} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 3, paddingLeft: 16 }}>
              <span style={{ fontSize: 10 }}>{CATEGORY_ICONS[cat] || '⚙️'}</span>
              <span style={{ fontSize: 10, color: CATEGORY_COLORS[cat] || '#8e8e93', fontWeight: 600 }}>{label}</span>
            </div>
            {catSkills.filter(matchSkill).map((skill) => {
              const added = nodes.some((n) => n.id === skill.name);
              return (
                <div
                  key={skill.name}
                  draggable={!added}
                  onDragStart={(e) => onDragStart(e, `skill:${skill.name}:${skill.label || skill.name}:${skill.category}:${skill.description}`)}
                  onClick={() => addSkillToCanvas(skill)}
                  style={{
                    background: added ? 'var(--bg-input)' : 'var(--bg-card)',
                    border: '1px solid var(--border)', borderRadius: 8, padding: '5px 10px', marginBottom: 2,
                    marginLeft: 16, cursor: added ? 'default' : 'grab', opacity: added ? 0.4 : 1,
                    fontSize: 11, color: 'var(--text-secondary)',
                  }}
                >
                  {skill.label || skill.name}
                </div>
              );
            })}
          </div>
        );
      })}

      {/* ── 适配器节点 ── */}
      <SectionHeader section="adapters" label="适配器 Adapter" icon="🧩" />
      {openSections.adapters && (
        <>
          {adapterTypes.map((at) => {
            const added = nodes.some((n) => n.type === 'adapter' && (n.data as any).adapterType === at.type);
            return (
              <div
                key={at.type}
                draggable={!added}
                onDragStart={(e) => onDragStart(e, `adapter:${at.type}:${at.name}`)}
                onClick={() => {
                  if (added) return;
                  const count = nodes.filter((n) => n.type === 'adapter').length;
                  addNode({
                    id: `adapter_${at.type}_${Date.now()}`,
                    type: 'adapter',
                    position: { x: 320, y: 400 + count * 100 },
                    data: { label: at.name, adapterType: at.type, adapterName: at.type, description: '', config: {}, outputKey: `${at.type}_result` },
                  });
                }}
                style={{
                  background: added ? 'var(--bg-input)' : 'var(--bg-card)',
                  border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', marginBottom: 4,
                  cursor: added ? 'default' : 'grab',
                  opacity: added ? 0.4 : 1,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: NODE_TYPE_COLORS.adapter }} />
                  <span style={{ color: 'var(--text)', fontSize: 12, fontWeight: 600 }}>{at.name}</span>
                </div>
                <div style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 16, marginTop: 1 }}>{at.description}</div>
              </div>
            );
          })}
          {adapterTypes.length === 0 && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px 12px' }}>暂无可用适配器</div>
          )}
        </>
      )}

      {/* ── 事件触发器 ── */}
      <SectionHeader section="events" label="事件触发 Event" icon="⚡" />
      {openSections.events && (
        <>
          {[
            { type: 'price_alert', label: '价格警报', desc: '股价达到阈值时触发' },
            { type: 'indicator_signal', label: '指标信号', desc: '技术指标产生信号时触发' },
            { type: 'news_event', label: '新闻事件', desc: '包含关键词的新闻触发' },
          ].map((evt) => {
            const added = nodes.some((n) => n.type === 'event_trigger' && (n.data as any).eventType === evt.type);
            return (
              <div
                key={evt.type}
                draggable={!added}
                onDragStart={(e) => onDragStart(e, `event_trigger:${evt.type}:${evt.label}`)}
                onClick={() => {
                  if (added) return;
                  const count = nodes.filter((n) => n.type === 'event_trigger').length;
                  addNode({
                    id: `trigger_${Date.now()}`,
                    type: 'event_trigger',
                    position: { x: 320, y: 400 + count * 100 },
                    data: { label: evt.label, eventType: evt.type, conditions: {}, workflowName: '', enabled: true },
                  });
                }}
                style={{
                  background: added ? 'var(--bg-input)' : 'var(--bg-card)',
                  border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', marginBottom: 4,
                  cursor: added ? 'default' : 'grab',
                  opacity: added ? 0.4 : 1,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: NODE_TYPE_COLORS.event_trigger }} />
                  <span style={{ color: 'var(--text)', fontSize: 12, fontWeight: 600 }}>{evt.label}</span>
                </div>
                <div style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 16, marginTop: 1 }}>{evt.desc}</div>
              </div>
            );
          })}
        </>
      )}

      {/* ── 总结研判 ── */}
      <SectionHeader section="summarizer" label="总结研判" icon="✦" />
      {openSections.summarizer && (
        <div
          draggable={!nodes.some((n) => n.type === 'summarizer')}
          onDragStart={(e) => onDragStart(e, 'summarizer:summarizer:总结研判')}
          onClick={addSummarizer}
          style={{
            background: nodes.some((n) => n.type === 'summarizer') ? 'var(--bg-input)' : 'var(--bg-card)',
            border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', marginBottom: 6,
            cursor: nodes.some((n) => n.type === 'summarizer') ? 'default' : 'grab',
            opacity: nodes.some((n) => n.type === 'summarizer') ? 0.4 : 1,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-purple)' }} />
            <span style={{ color: 'var(--text)', fontSize: 12, fontWeight: 600 }}>{t("sidebar.summarizer")}</span>
          </div>
        </div>
      )}

      {/* ── 保存/导出 ── */}
      {nodes.some((n) => n.type === 'analyst') && (
        <div style={{ display: 'flex', gap: 6, marginTop: 8, marginBottom: 6 }}>
          {showSave ? (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: '8px 12px', width: '100%' }}>
              <input autoFocus value={saveName} onChange={(e) => setSaveName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                placeholder={t("sidebar.input_workflow_name")}
                style={{ width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8, padding: '5px 8px', color: 'var(--text)', fontSize: 12, marginBottom: 6 }}
              />
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={handleSave} disabled={!saveName.trim()} style={{ flex: 1, background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 8, padding: '4px 0', fontSize: 11, fontWeight: 600, opacity: saveName.trim() ? 1 : 0.5 }}>{t("sidebar.save")}</button>
                <button onClick={() => { setShowSave(false); setSaveName(''); }} style={{ flex: 1, background: 'var(--bg-input)', color: 'var(--text-muted)', border: '1px solid var(--border)', borderRadius: 8, padding: '4px 0', fontSize: 11 }}>{t("sidebar.cancel")}</button>
              </div>
            </div>
          ) : (
            <>
              <button onClick={() => setShowSave(true)} style={{ flex: 1, background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 8, padding: '5px 0', fontSize: 11, fontWeight: 600, boxShadow: '0 2px 8px rgba(0,122,255,0.25)' }}>{t("sidebar.save")}</button>
              <button onClick={exportWorkflow} style={{ flex: 1, background: 'var(--bg-card)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: 8, padding: '5px 0', fontSize: 11, fontWeight: 600 }}>{t("sidebar.export")}</button>
              <button onClick={refreshTemplates} title={t("sidebar.refresh")} style={{ background: 'var(--bg-card)', color: 'var(--text-muted)', border: '1px solid var(--border)', borderRadius: 8, padding: '5px 8px', fontSize: 11 }}>↻</button>
            </>
          )}
        </div>
      )}

      {/* ── 分割线 + 预置模板 ── */}
      <div style={{ borderTop: '1px solid var(--border)', margin: '12px 0' }} />
      <SectionHeader section="templates" label="预置模板" icon="📋" />
      {openSections.templates && <WorkflowTemplates />}
    </div>
  );
}

/** 预置工作流模板列表 */
function WorkflowTemplates() {
  const workflows = useWorkflowStore((s) => s.workflows);
  const setWorkflows = useWorkflowStore((s) => s.setWorkflows);
  const loadFromTemplate = useWorkflowStore((s) => s.loadFromTemplate);
  const agents = useWorkflowStore((s) => s.agents);

  useEffect(() => {
    if (workflows.length === 0) {
      fetch('/api/workflows').then((r) => r.json()).then(setWorkflows).catch(console.error);
    }
  }, [workflows.length, setWorkflows]);

  return (
    <>
      {workflows.map((wf) => (
        <div
          key={wf.id}
          onClick={() => agents.length > 0 && loadFromTemplate(wf)}
          style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10,
            padding: '8px 12px', marginBottom: 4, cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--accent-blue)'; e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,122,255,0.1)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none'; }}
        >
          <div style={{ color: 'var(--text)', fontSize: 12, fontWeight: 600 }}>{wf.name}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: 10, marginTop: 2 }}>{wf.description}</div>
        </div>
      ))}
    </>
  );
}
