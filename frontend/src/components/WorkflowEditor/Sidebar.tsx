// frontend/src/components/WorkflowEditor/Sidebar.tsx
// 左侧边栏 — 可拖拽的 Agent 列表、总结研判节点、自定义 Agent、预置工作流模板

import { useEffect, useState, useCallback } from 'react';
import { useWorkflowStore } from '../../store/workflowStore';
import { getAgents } from '../../api/client';
import { t } from '../../i18n';
import { STANCE_COLORS } from '../../constants/theme';
// 自定义 Agent 的循环配色
const CUSTOM_COLORS = ['#34C759', '#007AFF', '#FF9500', '#AF52DE', '#5AC8FA', '#FF3B30', '#FF2D55', '#64D2FF', '#FFCC00'];

/**
 * Sidebar — 左侧边栏组件
 */
export function Sidebar() {
  const { agents, setAgents, nodes, addNode, saveWorkflow, exportWorkflow } = useWorkflowStore();
  const [showCustom, setShowCustom] = useState(false);
  const [customName, setCustomName] = useState('');
  const [showSave, setShowSave] = useState(false);
  const [saveName, setSaveName] = useState('');

  useEffect(() => {
    getAgents().then(setAgents).catch(console.error);
  }, [setAgents]);

  const onDragStart = (e: React.DragEvent, type: string, role: string, label?: string) => {
    e.dataTransfer.setData('application/reactflow', `${type}:${role}:${label || role}`);
    e.dataTransfer.effectAllowed = 'move';
  };

  const addAgentToCanvas = (role: string) => {
    if (nodes.some((n) => n.id === role)) return;
    const agent = agents.find((a) => a.role === role);
    const count = nodes.filter((n) => n.type === 'analyst').length;
    addNode({
      id: role, type: 'analyst',
      position: { x: 100 + (count % 3) * 280, y: 100 + Math.floor(count / 3) * 200 },
      data: { role, label: agent?.name || role, skills: agent?.current_skills || [] },
    });
  };

  const addSummarizerToCanvas = () => {
    if (nodes.some((n) => n.type === 'summarizer')) return;
    const count = nodes.filter((n) => n.type === 'analyst').length;
    addNode({
      id: 'summarizer', type: 'summarizer',
      position: { x: 100 + (count % 3) * 280, y: 100 + Math.floor(count / 3) * 200 + 200 },
      data: { role: 'summarizer', label: '总结研判', skills: [] },
    });
  };

  const addCustomAgent = () => {
    const name = customName.trim();
    if (!name) return;
    const existing = nodes.filter((n) => n.id.startsWith('custom_')).length;
    const id = `custom_${existing + 1}`;
    const count = nodes.filter((n) => n.type === 'analyst').length;
    addNode({
      id, type: 'analyst',
      position: { x: 100 + (count % 3) * 280, y: 100 + Math.floor(count / 3) * 200 },
      data: { role: id, label: name, skills: ['stock_info', 'kline_data'], isCustom: true },
    });
    setCustomName('');
    setShowCustom(false);
  };

  const hasSummarizer = nodes.some((n) => n.type === 'summarizer');
  const hasAgents = nodes.some((n) => n.type === 'analyst');

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

  return (
    <div style={{
      width: 220, background: 'var(--bg-panel)', borderRight: '1px solid var(--border)',
      padding: 12, overflowY: 'auto',
      backdropFilter: 'var(--blur)', WebkitBackdropFilter: 'var(--blur)',
    }}>
      {/* Agent 拖拽区标题 */}
      <div style={{
        color: 'var(--text-muted)', fontSize: 11, fontWeight: 600, marginBottom: 10,
        textTransform: 'uppercase', letterSpacing: 0.5,
      }}>
        {t("sidebar.drag_agent")}
      </div>

      {/* Agent 列表 */}
      {agents.map((agent) => {
        const color = STANCE_COLORS[agent.role] || '#8e8e93';
        const alreadyAdded = nodes.some((n) => n.id === agent.role);
        return (
          <div
            key={agent.role}
            draggable
            onDragStart={(e) => onDragStart(e, 'analyst', agent.role, agent.name)}
            onClick={() => addAgentToCanvas(agent.role)}
            style={{
              background: alreadyAdded ? 'var(--bg-input)' : 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 10, padding: '10px 12px', marginBottom: 6,
              cursor: alreadyAdded ? 'default' : 'grab', opacity: alreadyAdded ? 0.4 : 1,
              transition: 'all 0.2s',
              backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
              <span style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{agent.name}</span>
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 3, marginLeft: 16 }}>
              {agent.current_skills.length} {t("sidebar.skills_count")}
            </div>
          </div>
        );
      })}

      {/* 自定义 Agent 区域 */}
      {showCustom ? (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 10, padding: '10px 12px', marginBottom: 6,
          backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
        }}>
          <input
            autoFocus
            value={customName}
            onChange={(e) => setCustomName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addCustomAgent()}
            placeholder={t("sidebar.input_name")}
            style={{
              width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
              borderRadius: 8, padding: '5px 8px', color: 'var(--text)', fontSize: 12, marginBottom: 8,
            }}
          />
          <div style={{ display: 'flex', gap: 6 }}>
            <button
              onClick={addCustomAgent}
              disabled={!customName.trim()}
              style={{
                flex: 1, background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 8,
                padding: '5px 0', fontSize: 12, cursor: 'pointer', fontWeight: 600,
                opacity: customName.trim() ? 1 : 0.5,
              }}
            >{t("sidebar.add")}</button>
            <button
              onClick={() => { setShowCustom(false); setCustomName(''); }}
              style={{
                flex: 1, background: 'var(--bg-input)', color: 'var(--text-muted)', border: '1px solid var(--border)',
                borderRadius: 8, padding: '5px 0', fontSize: 12, cursor: 'pointer',
              }}
            >{t("sidebar.cancel")}</button>
          </div>
        </div>
      ) : (
        <div
          onClick={() => setShowCustom(true)}
          style={{
            background: 'var(--bg-card)', border: '1px dashed var(--border-strong)', borderRadius: 10,
            padding: '10px 12px', marginBottom: 6, cursor: 'pointer', textAlign: 'center',
            color: 'var(--text-muted)', fontSize: 12,
            backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
          }}
        >
          + {t("sidebar.custom_agent")}
        </div>
      )}

      {/* 总结研判节点 */}
      <div
        draggable
        onDragStart={(e) => onDragStart(e, 'summarizer', 'summarizer', '总结研判')}
        onClick={addSummarizerToCanvas}
        style={{
          background: hasSummarizer ? 'var(--bg-input)' : 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 10, padding: '10px 12px', marginBottom: 6,
          cursor: hasSummarizer ? 'default' : 'grab', opacity: hasSummarizer ? 0.4 : 1,
          transition: 'all 0.2s',
          backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-purple)' }} />
          <span style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{t("sidebar.summarizer")}</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 3, marginLeft: 16 }}>
          {t("sidebar.summarizer_desc")}
        </div>
      </div>

      {/* 保存/导出按钮 */}
      {hasAgents && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 6, marginTop: 8 }}>
          {showSave ? (
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10,
              padding: '10px 12px', width: '100%',
              backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
            }}>
              <input
                autoFocus
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                placeholder={t("sidebar.input_workflow_name")}
                style={{
                  width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '5px 8px', color: 'var(--text)', fontSize: 12, marginBottom: 8,
                }}
              />
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={handleSave} disabled={!saveName.trim()} style={{
                  flex: 1, background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 8,
                  padding: '5px 0', fontSize: 12, cursor: 'pointer', fontWeight: 600,
                  opacity: saveName.trim() ? 1 : 0.5,
                }}>{t("sidebar.save")}</button>
                <button onClick={() => { setShowSave(false); setSaveName(''); }} style={{
                  flex: 1, background: 'var(--bg-input)', color: 'var(--text-muted)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '5px 0', fontSize: 12, cursor: 'pointer',
                }}>{t("sidebar.cancel")}</button>
              </div>
            </div>
          ) : (
            <>
              <button
                onClick={() => setShowSave(true)}
                style={{
                  flex: 1, background: 'var(--accent-blue)', color: '#fff', border: 'none', borderRadius: 8,
                  padding: '6px 0', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  boxShadow: '0 2px 8px rgba(0, 122, 255, 0.25)',
                }}
              >{t("sidebar.save")}</button>
              <button
                onClick={exportWorkflow}
                style={{
                  flex: 1, background: 'var(--bg-card)', color: 'var(--text)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '6px 0', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
                }}
              >{t("sidebar.export")}</button>
              <button
                onClick={refreshTemplates}
                title={t("sidebar.refresh")}
                style={{
                  background: 'var(--bg-card)', color: 'var(--text-muted)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '6px 8px', fontSize: 12, cursor: 'pointer',
                }}
              >↻</button>
            </>
          )}
        </div>
      )}

      {/* 分割线 */}
      <div style={{ borderTop: '1px solid var(--border)', margin: '14px 0' }} />

      {/* 预置模板区标题 */}
      <div style={{
        color: 'var(--text-muted)', fontSize: 11, fontWeight: 600, marginBottom: 10,
        textTransform: 'uppercase', letterSpacing: 0.5,
      }}>
        {t("sidebar.templates")}
      </div>
      <WorkflowTemplates />
    </div>
  );
}

/**
 * WorkflowTemplates — 预置工作流模板列表
 */
function WorkflowTemplates() {
  const { workflows, setWorkflows, loadFromTemplate, agents } = useWorkflowStore();

  useEffect(() => {
    if (workflows.length === 0) {
      fetch('/api/workflows').then((r) => r.json()).then(setWorkflows).catch(console.error);
    }
  }, [workflows.length, setWorkflows, agents]);

  return (
    <>
      {workflows.map((wf) => (
        <div
          key={wf.id}
          onClick={() => agents.length > 0 && loadFromTemplate(wf)}
          style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10,
            padding: '10px 12px', marginBottom: 6, cursor: 'pointer',
            backdropFilter: 'var(--blur-light)', WebkitBackdropFilter: 'var(--blur-light)',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent-blue)';
            e.currentTarget.style.boxShadow = '0 2px 12px rgba(0, 122, 255, 0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          <div style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{wf.name}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 2 }}>{wf.description}</div>
        </div>
      ))}
    </>
  );
}
