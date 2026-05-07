// frontend/src/components/WorkflowEditor/Sidebar.tsx
// 左侧边栏 — 可拖拽的 Agent 列表、总结研判节点、自定义 Agent、预置工作流模板

import { useEffect, useState, useCallback } from 'react';
import { useWorkflowStore } from '../../store/workflowStore';
import { getAgents } from '../../api/client';
import { t } from '../../i18n';
import { STANCE_COLORS } from '../../constants/theme';
// 自定义 Agent 的循环配色
const CUSTOM_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#06b6d4', '#ef4444', '#ec4899', '#14b8a6', '#f97316'];

/**
 * Sidebar — 左侧边栏组件
 * 上半部分：可拖拽/点击添加的 Agent 列表 + 总结研判节点 + 自定义 Agent
 * 下半部分：预置工作流模板列表
 */
export function Sidebar() {
  const { agents, setAgents, nodes, addNode, saveWorkflow, exportWorkflow } = useWorkflowStore();
  const [showCustom, setShowCustom] = useState(false);   // 是否显示自定义 Agent 输入区
  const [customName, setCustomName] = useState('');        // 自定义 Agent 名称
  const [showSave, setShowSave] = useState(false);         // 是否显示保存对话框
  const [saveName, setSaveName] = useState('');            // 保存的工作流名称

  // 页面加载时从后端获取所有 Agent 信息
  useEffect(() => {
    getAgents().then(setAgents).catch(console.error);
  }, [setAgents]);

  /** 拖拽开始 — 将节点信息写入 dataTransfer，供画布 onDrop 读取 */
  const onDragStart = (e: React.DragEvent, type: string, role: string, label?: string) => {
    e.dataTransfer.setData('application/reactflow', `${type}:${role}:${label || role}`);
    e.dataTransfer.effectAllowed = 'move';
  };

  /** 点击添加 Agent 到画布（与拖拽等效的快捷方式） */
  const addAgentToCanvas = (role: string) => {
    if (nodes.some((n) => n.id === role)) return;  // 已添加则跳过
    const agent = agents.find((a) => a.role === role);
    const count = nodes.filter((n) => n.type === 'analyst').length;
    addNode({
      id: role,
      type: 'analyst',
      position: { x: 100 + (count % 3) * 280, y: 100 + Math.floor(count / 3) * 200 },
      data: { role, label: agent?.name || role, skills: agent?.current_skills || [] },
    });
  };

  /** 添加总结研判节点到画布 */
  const addSummarizerToCanvas = () => {
    if (nodes.some((n) => n.type === 'summarizer')) return;  // 只允许一个
    const count = nodes.filter((n) => n.type === 'analyst').length;
    addNode({
      id: 'summarizer',
      type: 'summarizer',
      position: { x: 100 + (count % 3) * 280, y: 100 + Math.floor(count / 3) * 200 + 200 },
      data: { role: 'summarizer', label: '总结研判', skills: [] },
    });
  };

  /** 添加自定义 Agent 到画布 */
  const addCustomAgent = () => {
    const name = customName.trim();
    if (!name) return;
    // 生成唯一 ID：custom_序号
    const existing = nodes.filter((n) => n.id.startsWith('custom_')).length;
    const id = `custom_${existing + 1}`;
    const count = nodes.filter((n) => n.type === 'analyst').length;
    addNode({
      id,
      type: 'analyst',
      position: { x: 100 + (count % 3) * 280, y: 100 + Math.floor(count / 3) * 200 },
      data: { role: id, label: name, skills: ['stock_info', 'kline_data'], isCustom: true },
    });
    setCustomName('');
    setShowCustom(false);
  };

  const hasSummarizer = nodes.some((n) => n.type === 'summarizer');
  const hasAgents = nodes.some((n) => n.type === 'analyst');

  /** 保存工作流到后端 */
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

  /** 刷新模板列表 */
  const refreshTemplates = useCallback(() => {
    fetch('/api/workflows').then((r) => r.json()).then(useWorkflowStore.getState().setWorkflows).catch(console.error);
  }, []);

  return (
    <div style={{ width: 220, background: 'var(--bg-panel)', borderRight: '1px solid var(--border)', padding: 16, overflowY: 'auto' }}>
      {/* Agent 拖拽区标题 */}
      <h3 style={{ color: 'var(--text)', fontSize: 14, marginBottom: 12 }}>{t("sidebar.drag_agent")}</h3>

      {/* Agent 列表 — 可拖拽或点击添加 */}
      {agents.map((agent) => {
        const color = STANCE_COLORS[agent.role] || '#6b7280';
        const alreadyAdded = nodes.some((n) => n.id === agent.role);
        return (
          <div
            key={agent.role}
            draggable
            onDragStart={(e) => onDragStart(e, 'analyst', agent.role, agent.name)}
            onClick={() => addAgentToCanvas(agent.role)}
            style={{
              background: alreadyAdded ? 'var(--bg-input)' : 'var(--bg-card)',
              border: `1px solid ${color}44`,
              borderRadius: 8, padding: '10px 12px', marginBottom: 8,
              cursor: alreadyAdded ? 'default' : 'grab', opacity: alreadyAdded ? 0.5 : 1,
              transition: 'all 0.15s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
              <span style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{agent.name}</span>
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 4, marginLeft: 16 }}>
              {agent.current_skills.length} {t("sidebar.skills_count")}
            </div>
          </div>
        );
      })}

      {/* 自定义 Agent 区域 */}
      {showCustom ? (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '10px 12px', marginBottom: 8 }}>
          <input
            autoFocus
            value={customName}
            onChange={(e) => setCustomName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addCustomAgent()}
            placeholder={t("sidebar.input_name")}
            style={{
              width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border-strong)',
              borderRadius: 4, padding: '4px 8px', color: 'var(--text)', fontSize: 12, marginBottom: 8,
            }}
          />
          <div style={{ display: 'flex', gap: 6 }}>
            <button
              onClick={addCustomAgent}
              disabled={!customName.trim()}
              style={{
                flex: 1, background: '#6366f1', color: '#fff', border: 'none', borderRadius: 4,
                padding: '4px 0', fontSize: 11, cursor: 'pointer', opacity: customName.trim() ? 1 : 0.5,
              }}
            >{t("sidebar.add")}</button>
            <button
              onClick={() => { setShowCustom(false); setCustomName(''); }}
              style={{
                flex: 1, background: 'var(--bg-input)', color: 'var(--text-muted)', border: 'none',
                borderRadius: 4, padding: '4px 0', fontSize: 11, cursor: 'pointer',
              }}
            >{t("sidebar.cancel")}</button>
          </div>
        </div>
      ) : (
        <div
          onClick={() => setShowCustom(true)}
          style={{
            background: 'var(--bg-card)', border: '1px dashed var(--border-strong)', borderRadius: 8,
            padding: '10px 12px', marginBottom: 8, cursor: 'pointer', textAlign: 'center',
            color: 'var(--text-muted)', fontSize: 12,
          }}
        >
          {t("sidebar.custom_agent")}
        </div>
      )}

      {/* 总结研判节点 — 可拖拽或点击添加（仅允许一个） */}
      <div
        draggable
        onDragStart={(e) => onDragStart(e, 'summarizer', 'summarizer', '总结研判')}
        onClick={addSummarizerToCanvas}
        style={{
          background: hasSummarizer ? 'var(--bg-input)' : 'var(--bg-card)',
          border: '1px solid #a78bfa44',
          borderRadius: 8, padding: '10px 12px', marginBottom: 8,
          cursor: hasSummarizer ? 'default' : 'grab', opacity: hasSummarizer ? 0.5 : 1,
          transition: 'all 0.15s',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#a78bfa' }} />
          <span style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{t("sidebar.summarizer")}</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 4, marginLeft: 16 }}>
          {t("sidebar.summarizer_desc")}
        </div>
      </div>

      {/* 保存/导出按钮 */}
      {hasAgents && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
          {showSave ? (
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-strong)', borderRadius: 8,
              padding: '10px 12px', width: '100%',
            }}>
              <input
                autoFocus
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                placeholder={t("sidebar.input_workflow_name")}
                style={{
                  width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border-strong)',
                  borderRadius: 4, padding: '4px 8px', color: 'var(--text)', fontSize: 12, marginBottom: 8,
                }}
              />
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={handleSave} disabled={!saveName.trim()} style={{
                  flex: 1, background: '#6366f1', color: '#fff', border: 'none', borderRadius: 4,
                  padding: '4px 0', fontSize: 11, cursor: 'pointer', opacity: saveName.trim() ? 1 : 0.5,
                }}>保存</button>
                <button onClick={() => { setShowSave(false); setSaveName(''); }} style={{
                  flex: 1, background: 'var(--bg-input)', color: 'var(--text-muted)', border: 'none',
                  borderRadius: 4, padding: '4px 0', fontSize: 11, cursor: 'pointer',
                }}>{t("sidebar.cancel")}</button>
              </div>
            </div>
          ) : (
            <>
              <button
                onClick={() => setShowSave(true)}
                style={{
                  flex: 1, background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6,
                  padding: '6px 0', fontSize: 11, fontWeight: 600, cursor: 'pointer',
                }}
              >{t("sidebar.save")}</button>
              <button
                onClick={exportWorkflow}
                style={{
                  flex: 1, background: 'var(--bg-card)', color: 'var(--text)', border: '1px solid var(--border-strong)',
                  borderRadius: 6, padding: '6px 0', fontSize: 11, fontWeight: 600, cursor: 'pointer',
                }}
              >{t("sidebar.export")}</button>
              <button
                onClick={refreshTemplates}
                title={t("sidebar.refresh")}
                style={{
                  background: 'var(--bg-card)', color: 'var(--text-muted)', border: '1px solid var(--border-strong)',
                  borderRadius: 6, padding: '6px 8px', fontSize: 11, cursor: 'pointer',
                }}
              >🔄</button>
            </>
          )}
        </div>
      )}

      {/* 分割线 */}
      <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '16px 0' }} />

      {/* 预置模板区标题 */}
      <h3 style={{ color: 'var(--text)', fontSize: 14, marginBottom: 12 }}>{t("sidebar.templates")}</h3>
      <WorkflowTemplates />
    </div>
  );
}

/**
 * WorkflowTemplates — 预置工作流模板列表
 * 从后端加载模板列表，点击即可加载到画布
 */
function WorkflowTemplates() {
  const { workflows, setWorkflows, loadFromTemplate, agents } = useWorkflowStore();

  // 首次渲染时加载工作流模板
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
            background: 'var(--bg-card)', border: '1px solid var(--border-strong)', borderRadius: 8,
            padding: '10px 12px', marginBottom: 8, cursor: 'pointer',
          }}
        >
          <div style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{wf.name}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 2 }}>{wf.description}</div>
        </div>
      ))}
    </>
  );
}
