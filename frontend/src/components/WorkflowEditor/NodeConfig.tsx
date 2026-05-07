// frontend/src/components/WorkflowEditor/NodeConfig.tsx
// 节点配置面板 — 右侧面板，展示选中 Agent 的技能配置和额外提示词

import { useWorkflowStore } from '../../store/workflowStore';
import { SkillPicker } from './SkillPicker';

/**
 * NodeConfig — 节点配置面板组件
 * 未选中节点时显示引导提示，选中分析师节点后展示技能选择器和额外提示词输入框
 */
export function NodeConfig() {
  const { selectedNodeId, nodes, updateNodeData } = useWorkflowStore();
  const node = nodes.find((n) => n.id === selectedNodeId);

  // 未选中分析师节点 — 显示引导提示
  if (!node || node.type !== 'analyst') {
    return (
      <div style={{ width: 280, background: 'var(--bg-panel)', borderLeft: '1px solid var(--border)', padding: 16 }}>
        <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
          点击 Agent 节点<br />配置技能和参数
        </div>
      </div>
    );
  }

  const data = node.data as any;

  return (
    <div style={{ width: 280, background: 'var(--bg-panel)', borderLeft: '1px solid var(--border)', padding: 16, overflowY: 'auto' }}>
      {/* 节点标题：角色名称 */}
      <h3 style={{ color: 'var(--text)', fontSize: 15, marginBottom: 4 }}>⚙️ {data.label}</h3>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 16 }}>角色: {data.role}</div>

      {/* 技能选择器 */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ color: 'var(--text-secondary)', fontSize: 12, display: 'block', marginBottom: 4 }}>Skills 技能配置</label>
        <SkillPicker
          role={data.role}
          currentSkills={data.skills || []}
          onUpdate={(skills) => updateNodeData(node.id, { skills })}
        />
      </div>

      {/* 额外提示词输入框 */}
      <div>
        <label style={{ color: 'var(--text-secondary)', fontSize: 12, display: 'block', marginBottom: 4 }}>额外提示词</label>
        <textarea
          value={data.extra_prompt || ''}
          onChange={(e) => updateNodeData(node.id, { extra_prompt: e.target.value })}
          placeholder="可选：针对本次分析的额外指令..."
          style={{
            width: '100%', minHeight: 80, background: 'var(--bg-input)', border: '1px solid var(--border-strong)',
            borderRadius: 6, padding: 8, color: 'var(--text)', fontSize: 12, resize: 'vertical',
          }}
        />
      </div>
    </div>
  );
}
