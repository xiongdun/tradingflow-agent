// frontend/src/components/Schedule/SchedulePanel.tsx
// 定时任务面板 — 创建/管理定时分析任务

import { useState, useEffect, useCallback } from 'react';
import { t } from '../../i18n';

interface ScheduleTask {
  id: number;
  symbol: string;
  market: string;
  workflow: string;
  schedule_type: string;
  schedule_time: string;
  interval_minutes: number;
  enabled: number;
  last_run: string | null;
  next_run: string | null;
  created_at: string;
}

function getMarketLabel(m: string) { return t(`market.${m}`) || m; }
function getTypeLabel(s: string) { return t(`schedule.${s}`) || s; }

export function SchedulePanel() {
  const [tasks, setTasks] = useState<ScheduleTask[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    symbol: '', market: 'a_share', workflow: 'deep_analysis',
    schedule_type: 'daily', schedule_time: '09:00', interval_minutes: 60,
  });

  const load = useCallback(async () => {
    try {
      const resp = await fetch('/api/schedules');
      const data = await resp.json();
      setTasks(data.tasks || []);
    } catch { setTasks([]); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    if (!form.symbol.trim()) return;
    try {
      const resp = await fetch('/api/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (resp.ok) { setShowForm(false); setForm({ symbol: '', market: 'a_share', workflow: 'deep_analysis', schedule_type: 'daily', schedule_time: '09:00', interval_minutes: 60 }); load(); }
    } catch {}
  };

  const toggle = async (task: ScheduleTask) => {
    await fetch(`/api/schedules/${task.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: task.enabled ? 0 : 1 }),
    });
    load();
  };

  const remove = async (id: number) => {
    await fetch(`/api/schedules/${id}`, { method: 'DELETE' });
    load();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg)' }}>
      {/* 顶部操作栏 */}
      <div style={{ display: 'flex', gap: 8, padding: '8px 16px', borderBottom: '1px solid var(--border)', background: 'var(--bg-panel)', alignItems: 'center' }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>{t("schedule.title")}</span>
        <div style={{ flex: 1 }} />
        <button onClick={() => setShowForm(!showForm)} style={primaryBtn}>
          {showForm ? t("schedule.cancel") : t("schedule.create")}
        </button>
      </div>

      {/* 创建表单 */}
      {showForm && (
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', background: 'var(--bg-card)', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} placeholder={t("watchlist.placeholder_symbol")} style={inputStyle} />
          <select value={form.market} onChange={(e) => setForm({ ...form, market: e.target.value })} style={inputStyle}>
            <option value="a_share">{t("market.a_share")}</option>
            <option value="h_stock">{t("market.h_stock")}</option>
            <option value="us_stock">{t("market.us_stock")}</option>
          </select>
          <select value={form.workflow} onChange={(e) => setForm({ ...form, workflow: e.target.value })} style={inputStyle}>
            <option value="deep_analysis">{t("schedule.deep_analysis")}</option>
            <option value="quick_scan">{t("schedule.quick_scan")}</option>
            <option value="debate">{t("schedule.debate")}</option>
          </select>
          <select value={form.schedule_type} onChange={(e) => setForm({ ...form, schedule_type: e.target.value })} style={inputStyle}>
            <option value="daily">{t("schedule.daily")}</option>
            <option value="interval">{t("schedule.interval")}</option>
            <option value="once">{t("schedule.once")}</option>
          </select>
          {form.schedule_type === 'daily' && (
            <input type="time" value={form.schedule_time} onChange={(e) => setForm({ ...form, schedule_time: e.target.value })} style={inputStyle} />
          )}
          {form.schedule_type === 'interval' && (
            <input type="number" min={5} value={form.interval_minutes} onChange={(e) => setForm({ ...form, interval_minutes: +e.target.value })} placeholder="间隔(分)" style={{ ...inputStyle, width: 80 }} />
          )}
          <button onClick={create} style={primaryBtn}>{t("common.create")}</button>
        </div>
      )}

      {/* 任务列表 */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {tasks.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', paddingTop: 40 }}>{t("schedule.empty")}</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("schedule.stock")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.market")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("schedule.workflow_label")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("schedule.schedule_label")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("schedule.next_run")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("schedule.last_run")}</th>
                <th style={{ textAlign: 'center', padding: '6px 8px' }}>{t("schedule.status")}</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>{t("history.action")}</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '6px 8px', fontWeight: 600 }}>{task.symbol}</td>
                  <td style={{ padding: '6px 8px' }}>{getMarketLabel(task.market)}</td>
                  <td style={{ padding: '6px 8px' }}>{task.workflow}</td>
                  <td style={{ padding: '6px 8px' }}>
                    {getTypeLabel(task.schedule_type)}
                    {task.schedule_type === 'daily' && ` ${task.schedule_time}`}
                    {task.schedule_type === 'interval' && ` ${task.interval_minutes}min`}
                  </td>
                  <td style={{ padding: '6px 8px', color: 'var(--text-secondary)', fontSize: 11 }}>
                    {task.next_run ? new Date(task.next_run).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-'}
                  </td>
                  <td style={{ padding: '6px 8px', color: 'var(--text-secondary)', fontSize: 11 }}>
                    {task.last_run ? new Date(task.last_run).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-'}
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'center' }}>
                    <span style={{
                      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
                      background: task.enabled ? '#10b981' : '#6b7280',
                    }} />
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <button onClick={() => toggle(task)} style={{ ...primaryBtn, marginRight: 4, background: task.enabled ? '#f59e0b' : '#10b981' }}>
                      {task.enabled ? '暂停' : '启用'}
                    </button>
                    <button onClick={() => remove(task.id)} style={{ ...primaryBtn, background: '#ef4444' }}>{t("common.delete")}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: 'var(--bg-input)', border: '1px solid var(--border-strong)', borderRadius: 4,
  padding: '4px 8px', color: 'var(--text)', fontSize: 12, width: 120,
};

const primaryBtn: React.CSSProperties = {
  background: '#6366f1', color: '#fff', border: 'none', borderRadius: 4,
  padding: '4px 14px', fontSize: 12, cursor: 'pointer', fontWeight: 600,
};
