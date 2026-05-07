// frontend/src/components/WorkflowEditor/SkillPicker.tsx
// 技能选择器 — 按类别分组展示所有技能，支持勾选/取消勾选并同步到后端

import { useState, useEffect } from 'react';
import { getSkills, setAgentSkills } from '../../api/client';
import type { SkillInfo } from '../../types';

/** 组件 Props — 角色标识、当前技能列表、更新回调 */
interface Props {
  role: string;                    // Agent 角色标识
  currentSkills: string[];         // 当前已选技能
  onUpdate: (skills: string[]) => void;  // 技能更新回调
}

/**
 * SkillPicker — 技能选择器组件
 * 从后端加载所有技能，按类别分组展示，勾选时自动同步到后端 Agent 配置
 */
export function SkillPicker({ role, currentSkills, onUpdate }: Props) {
  const [allSkills, setAllSkills] = useState<SkillInfo[]>([]);  // 所有可用技能
  const [selected, setSelected] = useState<Set<string>>(new Set(currentSkills));  // 已选技能集合

  // 首次渲染时加载所有技能
  useEffect(() => {
    getSkills().then(setAllSkills).catch(console.error);
  }, []);

  // 当外部 currentSkills 变化时同步选中状态
  useEffect(() => {
    setSelected(new Set(currentSkills));
  }, [currentSkills]);

  /** 切换技能选中状态 — 更新本地状态并同步到后端 */
  const toggle = async (name: string) => {
    const next = new Set(selected);
    if (next.has(name)) next.delete(name); else next.add(name);
    setSelected(next);
    const skills = Array.from(next);
    try {
      await setAgentSkills(role, skills);  // 调用后端 API 更新 Agent 技能
      onUpdate(skills);                    // 通知父组件
    } catch (e) { console.error(e); }
  };

  // 提取所有技能类别（去重）
  const categories = [...new Set(allSkills.map((s) => s.category))];

  return (
    <div style={{ maxHeight: 300, overflowY: 'auto' }}>
      {/* 按类别分组渲染技能列表 */}
      {categories.map((cat) => (
        <div key={cat} style={{ marginBottom: 10 }}>
          {/* 类别标题 */}
          <div style={{
            color: 'var(--text-muted)', fontSize: 11, fontWeight: 600, marginBottom: 4,
          }}>
            {cat}
          </div>
          {/* 该类别下的技能复选框列表 */}
          {allSkills.filter((s) => s.category === cat).map((skill) => (
            <label
              key={skill.name}
              style={{
                display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0',
                cursor: 'pointer', fontSize: 12, color: 'var(--text-subtle)',
              }}
            >
              <input
                type="checkbox"
                checked={selected.has(skill.name)}
                onChange={() => toggle(skill.name)}
                style={{ accentColor: 'var(--accent-blue)' }}
              />
              <span>{skill.name}</span>
            </label>
          ))}
        </div>
      ))}
    </div>
  );
}
