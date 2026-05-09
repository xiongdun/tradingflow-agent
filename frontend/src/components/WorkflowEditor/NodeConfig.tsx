// frontend/src/components/WorkflowEditor/NodeConfig.tsx
// 右侧详情面板 — 选中任意节点时展示对应信息，Agent 节点额外展示分析进度与结果

import { useState, memo } from 'react';
import { useWorkflowStore } from '../../store/workflowStore';
import type { AgentOpinion } from '../../types';
import { t } from '../../i18n';
import { STANCE_COLORS, NODE_TYPE_COLORS, ADAPTER_ICONS, EVENT_ICONS, CATEGORY_ICONS } from '../../constants/theme';

const stanceEmoji: Record<string, string> = {
  bullish: '🟢', bearish: '🔴', neutral: '🟡',
};

const statusColorMap: Record<string, string> = {
  idle: '#8e8e93', running: '#FF9500', done: '#34C759', error: '#FF3B30',
};

/** 通用面板容器样式 */
const panelStyle: React.CSSProperties = {
  width: '100%', height: '100%', background: 'var(--bg-panel)', borderLeft: '1px solid var(--border)',
  padding: 16, overflowY: 'auto', boxSizing: 'border-box',
  backdropFilter: 'var(--blur)', WebkitBackdropFilter: 'var(--blur)',
};

/** 通用信息卡片样式 */
const cardStyle: React.CSSProperties = {
  background: 'var(--bg-card)', borderRadius: 10, border: '1px solid var(--border)',
  padding: 12, marginBottom: 14,
};

/** 分割线 */
const divider: React.CSSProperties = {
  height: 1, background: 'var(--border)', margin: '12px 0',
};

/**
 * NodeConfig — 右侧详情面板
 * 根据选中节点类型展示不同内容
 */
export function NodeConfig() {
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId);
  const nodes = useWorkflowStore((s) => s.nodes);
  const node = nodes.find((n) => n.id === selectedNodeId);

  // 未选中任何节点
  if (!node) {
    return (
      <div style={panelStyle}>
        <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', marginTop: 40, lineHeight: 1.6 }}>
          点击画布节点<br />查看详细信息
        </div>
      </div>
    );
  }

  const data = node.data as any;

  switch (node.type) {
    case 'analyst':
      return <AnalystPanel data={data} nodeId={node.id} />;
    case 'skill':
      return <SkillPanel data={data} />;
    case 'input':
      return <InputPanel data={data} />;
    case 'config':
      return <ConfigPanel data={data} />;
    case 'summarizer':
      return <SummarizerPanel data={data} />;
    case 'adapter':
      return <AdapterPanel data={data} nodeId={node.id} />;
    case 'event_trigger':
      return <EventTriggerPanel data={data} nodeId={node.id} />;
    default:
      return (
        <div style={panelStyle}>
          <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
            未知节点类型: {node.type}
          </div>
        </div>
      );
  }
}

// ══════════════════════════════════════════════════════════════════════
//  Analyst 面板 — 角色信息 + 分析进度 + 结果 + 额外提示词
// ══════════════════════════════════════════════════════════════════════

function AnalystPanel({ data, nodeId }: { data: any; nodeId: string }) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData);
  const role: string = data.role;
  const label: string = data.label;
  const color = STANCE_COLORS[role] || '#8e8e93';
  const progress = useWorkflowStore((s) => s.agentProgressMap[role]);
  const status = progress?.status || 'idle';
  const messages = progress?.messages || [];
  const opinion = progress?.opinion;

  return (
    <div style={panelStyle}>
      {/* 头部 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15, flex: 1 }}>{label}</span>
        <StatusBadge status={status} />
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 14 }}>角色: {role}</div>

      {/* 已配置技能 */}
      {data.skills?.length > 0 && (
        <div style={cardStyle}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>🔧 已配置技能</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {data.skills.map((sk: string) => (
              <span key={sk} style={{
                background: `${color}15`, color, borderRadius: 6, padding: '2px 8px',
                fontSize: 10, fontWeight: 500,
              }}>{sk}</span>
            ))}
          </div>
        </div>
      )}

      {/* 分析进度 */}
      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
          📡 {t('agent_modal.status_' + status) || status}
        </div>

        {status === 'idle' && (
          <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '12px 0' }}>
            {t('agent_modal.idle')}
          </div>
        )}

        {status === 'running' && (
          <div>
            {messages.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: '8px 0' }}>
                {t('agent_modal.waiting')}
              </div>
            ) : (
              <div style={{ maxHeight: 180, overflow: 'auto' }}>
                {messages.map((msg: string, i: number) => (
                  <div key={i} style={{
                    fontSize: 11, color: 'var(--text-secondary)', padding: '4px 0',
                    borderBottom: '1px solid var(--border)',
                  }}>
                    <span style={{ color: 'var(--accent-orange)', marginRight: 4 }}>›</span>{msg}
                  </div>
                ))}
              </div>
            )}
            <div style={{
              height: 2, borderRadius: 1, marginTop: 8,
              background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
              animation: 'pulse-bar 1.5s ease-in-out infinite',
            }} />
          </div>
        )}

        {status === 'error' && (
          <div style={{ color: 'var(--accent-red)', fontSize: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>❌ {t('agent_modal.error')}</div>
            {messages.length > 0 && (
              <div style={{
                background: 'rgba(255,59,48,0.08)', borderRadius: 8, padding: 10, fontSize: 11,
                border: '1px solid rgba(255,59,48,0.15)',
              }}>
                {messages[messages.length - 1]}
              </div>
            )}
          </div>
        )}

        {status === 'done' && !opinion && (
          <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '12px 0' }}>
            {t('agent_modal.done_no_result')}
          </div>
        )}
      </div>

      {/* 分析结果 */}
      {status === 'done' && opinion && <OpinionDetail opinion={opinion} color={color} />}

      {/* 额外提示词 */}
      <div style={divider} />
      <label style={{ color: 'var(--text-secondary)', fontSize: 12, display: 'block', marginBottom: 6, fontWeight: 500 }}>
        额外提示词
      </label>
      <textarea
        value={data.extra_prompt || ''}
        onChange={(e) => updateNodeData(nodeId, { extra_prompt: e.target.value })}
        placeholder="可选：针对本次分析的额外指令..."
        style={{
          width: '100%', minHeight: 72, background: 'var(--bg-input)', border: '1px solid var(--border)',
          borderRadius: 10, padding: 10, color: 'var(--text)', fontSize: 12, resize: 'vertical',
        }}
      />
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
//  Skill 面板 — 技能名称、类别、描述、参数说明
// ══════════════════════════════════════════════════════════════════════

function SkillPanel({ data }: { data: any }) {
  const meta = useWorkflowStore((s) => s.skills.find((sk) => sk.name === data.skillName));

  return (
    <div style={panelStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16 }}>{CATEGORY_ICONS[data.category] || '⚙️'}</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15 }}>{data.label}</span>
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 14 }}>
        标识: <span style={{ fontFamily: 'monospace' }}>{data.skillName}</span>
        <span style={{ margin: '0 6px' }}>·</span>
        类别: {data.category}
      </div>

      {/* 描述 */}
      {(meta?.description || data.description) && (
        <div style={cardStyle}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>📖 描述</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            {meta?.description || data.description}
          </div>
        </div>
      )}

      {/* 支持市场 */}
      {meta?.markets && meta.markets.length > 0 && (
        <div style={cardStyle}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>🌍 支持市场</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {meta.markets.map((m: string) => (
              <span key={m} style={{
                background: 'var(--bg-input)', borderRadius: 6, padding: '2px 8px',
                fontSize: 10, color: 'var(--text-secondary)',
              }}>{m}</span>
            ))}
          </div>
        </div>
      )}

      {/* 参数说明 */}
      {meta?.params && Object.keys(meta.params).length > 0 && (
        <div style={cardStyle}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>⚙️ 参数</div>
          {Object.entries(meta.params).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--accent-blue)' }}>{k}</span>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{String(v)}</span>
            </div>
          ))}
        </div>
      )}

      {/* 依赖技能 */}
      {meta?.depends_on && meta.depends_on.length > 0 && (
        <div style={cardStyle}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>🔗 依赖技能</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {meta.depends_on.map((d: string) => (
              <span key={d} style={{
                background: 'rgba(255,149,0,0.1)', color: '#FF9500', borderRadius: 6,
                padding: '2px 8px', fontSize: 10, fontWeight: 500,
              }}>{d}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
//  Input 面板 — 股票代码、市场类型
// ══════════════════════════════════════════════════════════════════════

function InputPanel({ data }: { data: any }) {
  const marketLabels: Record<string, string> = { a_share: 'A股', h_stock: '港股', us_stock: '美股' };

  return (
    <div style={panelStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16, color: 'var(--accent-green)' }}>◆</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15 }}>输入节点</span>
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 14 }}>定义分析目标股票</div>

      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>📋 配置信息</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>股票代码</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-green)', fontFamily: 'monospace' }}>
            {data.symbol || '—'}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>市场</span>
          <span style={{ fontSize: 12, color: 'var(--text)' }}>
            {marketLabels[data.market] || data.market}
          </span>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
//  Config 面板 — K线周期、历史天数
// ══════════════════════════════════════════════════════════════════════

function ConfigPanel({ data }: { data: any }) {
  const periodLabels: Record<string, string> = { daily: '日K', weekly: '周K', monthly: '月K' };

  return (
    <div style={panelStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16, color: 'var(--accent-orange)' }}>⚙</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15 }}>参数配置</span>
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 14 }}>全局分析参数</div>

      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>📋 参数信息</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>K线周期</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>
            {periodLabels[data.period] || data.period}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>历史天数</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>
            {data.days} 天
          </span>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
//  Summarizer 面板 — 总结研判说明
// ══════════════════════════════════════════════════════════════════════

function SummarizerPanel({ data }: { data: any }) {
  return (
    <div style={panelStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16, color: 'var(--accent-purple)' }}>✦</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15 }}>{data.label || '总结研判'}</span>
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 14 }}>综合所有分析师意见</div>

      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>📖 功能说明</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          总结研判节点汇集所有分析师的独立观点，进行交叉验证和综合评估，最终生成统一的投资研判报告。
        </div>
      </div>

      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>📊 输出内容</div>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
          • 整体立场（看多/看空/中性）<br />
          • 综合置信度<br />
          • 分析师共识与分歧<br />
          • 关键风险与投资机会<br />
          • 操作建议
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
//  Adapter 面板 — 外部适配器节点配置说明
// ══════════════════════════════════════════════════════════════════════

const ADAPTER_DESCRIPTIONS: Record<string, string> = {
  http: '将外部 REST API 包装为工作流节点，支持 URL 模板变量和 Body 映射',
  script: '执行本地 Python/JS 脚本，支持指定脚本路径和入口函数',
  docker: '在 Docker 容器中运行外部程序，支持镜像配置和环境变量',
  mcp: '通过 MCP (Model Context Protocol) 连接外部工具服务器',
  langchain: '包装 LangChain Tool 为工作流节点',
  function: '将任意 async 函数包装为工作流节点',
};

const AdapterPanel = memo(function AdapterPanel({ data, nodeId }: { data: any; nodeId: string }) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData);
  const color = NODE_TYPE_COLORS.adapter;
  const icon = ADAPTER_ICONS[data.adapterType] || '🧩';
  const desc = ADAPTER_DESCRIPTIONS[data.adapterType] || '通用适配器';
  const [configError, setConfigError] = useState<string | null>(null);

  return (
    <div style={panelStyle}>
      {/* 头部 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16 }}>{icon}</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15, flex: 1 }}>
          {data.label || data.adapterName || '适配器'}
        </span>
        <span style={{
          background: `${color}18`, color, borderRadius: 8, padding: '2px 8px',
          fontSize: 10, fontWeight: 600,
        }}>
          {data.adapterType}
        </span>
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 14 }}>
        类型: <span style={{ fontFamily: 'monospace' }}>{data.adapterType}</span>
        {data.outputKey && (
          <>
            <span style={{ margin: '0 6px' }}>·</span>
            输出: <span style={{ fontFamily: 'monospace', color: 'var(--accent-blue)' }}>{data.outputKey}</span>
          </>
        )}
      </div>

      {/* 功能说明 */}
      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>📖 功能说明</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          {desc}
        </div>
      </div>

      {/* 输出字段 */}
      {data.outputKey && (
        <div style={cardStyle}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>📤 输出字段</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Output Key</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-blue)', fontFamily: 'monospace' }}>
              {data.outputKey}
            </span>
          </div>
        </div>
      )}

      {/* 配置 */}
      <div style={divider} />
      <label style={{ color: 'var(--text-secondary)', fontSize: 12, display: 'block', marginBottom: 6, fontWeight: 500 }}>
        配置
      </label>
      <textarea
        value={JSON.stringify(data.config || {}, null, 2)}
        onChange={(e) => {
          try {
            updateNodeData(nodeId, { config: JSON.parse(e.target.value) });
            setConfigError(null);
          } catch (err) {
            setConfigError(err instanceof Error ? err.message : 'JSON 格式错误');
          }
        }}
        placeholder='{"url": "...", "method": "GET"}'
        style={{
          width: '100%', minHeight: 80,
          background: 'var(--bg-input)',
          border: `1px solid ${configError ? 'var(--accent-red)' : 'var(--border)'}`,
          borderRadius: 10, padding: 10, color: 'var(--text)', fontSize: 11,
          fontFamily: 'monospace', resize: 'vertical',
        }}
      />
      {configError && (
        <div style={{ fontSize: 10, color: 'var(--accent-red)', marginTop: 4, lineHeight: 1.4 }}>
          ⚠ {configError}
        </div>
      )}
    </div>
  );
});

// ══════════════════════════════════════════════════════════════════════
//  EventTrigger 面板 — 事件触发器节点配置
// ══════════════════════════════════════════════════════════════════════

const EVENT_DESCRIPTIONS: Record<string, string> = {
  price_alert: '当股票价格达到设定条件时自动触发工作流，支持价格上限、下限、涨跌幅等条件',
  indicator_signal: '当技术指标（MACD、KDJ、RSI等）产生特定信号时自动触发',
  news_event: '当新闻中包含指定关键词时自动触发，支持多关键词组合匹配',
  custom: '自定义事件触发器，可通过 API 接口手动触发',
};

const EventTriggerPanel = memo(function EventTriggerPanel({ data, nodeId }: { data: any; nodeId: string }) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData);
  const color = NODE_TYPE_COLORS.event_trigger;
  const icon = EVENT_ICONS[data.eventType] || '⚡';
  const desc = EVENT_DESCRIPTIONS[data.eventType] || '自定义事件触发';
  const enabled = data.enabled !== false;

  return (
    <div style={panelStyle}>
      {/* 头部 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 16 }}>{icon}</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15, flex: 1 }}>
          {data.label || '事件触发'}
        </span>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: enabled ? color : 'var(--text-muted)',
          boxShadow: enabled ? `0 0 6px ${color}88` : 'none',
        }} />
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 14 }}>
        类型: <span style={{ fontFamily: 'monospace' }}>{data.eventType}</span>
        {data.workflowName && (
          <>
            <span style={{ margin: '0 6px' }}>→</span>
            工作流: <span style={{ fontFamily: 'monospace', color: 'var(--accent-blue)' }}>{data.workflowName}</span>
          </>
        )}
      </div>

      {/* 功能说明 */}
      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>📖 功能说明</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          {desc}
        </div>
      </div>

      {/* 触发条件 */}
      {data.conditions && Object.keys(data.conditions).length > 0 && (
        <div style={cardStyle}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>⚙ 触发条件</div>
          {Object.entries(data.conditions).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--accent-orange)' }}>{k}</span>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{String(v)}</span>
            </div>
          ))}
        </div>
      )}

      {/* 关联工作流 */}
      <div style={cardStyle}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>🔗 关联工作流</div>
        <input
          value={data.workflowName || ''}
          onChange={(e) => updateNodeData(nodeId, { workflowName: e.target.value })}
          placeholder="输入工作流名称..."
          style={{
            width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '6px 10px', color: 'var(--text)', fontSize: 12,
          }}
        />
      </div>

      {/* 启用开关 */}
      <div style={divider} />
      <div
        onClick={() => updateNodeData(nodeId, { enabled: !enabled })}
        role="switch"
        aria-checked={enabled}
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); updateNodeData(nodeId, { enabled: !enabled }); } }}
        style={{
          display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
          padding: '8px 0', outline: 'none',
        }}
      >
        <div style={{
          width: 36, height: 20, borderRadius: 10,
          background: enabled ? color : 'var(--text-muted)',
          position: 'relative', transition: 'background 0.2s',
        }}>
          <div style={{
            width: 16, height: 16, borderRadius: '50%', background: '#fff',
            position: 'absolute', top: 2, left: enabled ? 18 : 2,
            transition: 'left 0.2s',
          }} />
        </div>
        <span style={{ fontSize: 12, color: enabled ? 'var(--text)' : 'var(--text-muted)' }}>
          {enabled ? '已启用' : '已禁用'}
        </span>
      </div>
    </div>
  );
});

// ══════════════════════════════════════════════════════════════════════
//  通用子组件
// ══════════════════════════════════════════════════════════════════════

/** 状态徽章 */
function StatusBadge({ status }: { status: string }) {
  const c = statusColorMap[status] || '#8e8e93';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: `${c}18`, color: c,
      borderRadius: 8, padding: '2px 8px', fontSize: 10, fontWeight: 600,
    }}>
      {t('agent_modal.status_' + status) || status}
    </span>
  );
}

/** 分析意见详情 */
function OpinionDetail({ opinion, color }: { opinion: AgentOpinion; color: string }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{
        display: 'flex', gap: 16, alignItems: 'center', marginBottom: 12,
        background: `${color}10`, borderRadius: 10, padding: '10px 14px',
        border: `1px solid ${color}20`,
      }}>
        <span style={{ fontSize: 14 }}>
          {stanceEmoji[opinion.stance] || ''} {t('report.stance_' + opinion.stance) || opinion.stance}
        </span>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-blue)' }}>
          {t('report.confidence')}: {((opinion.confidence || 0) * 100).toFixed(0)}%
        </span>
      </div>

      {opinion.summary && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t('agent_modal.summary')}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            {opinion.summary}
          </div>
        </div>
      )}

      {opinion.key_points && opinion.key_points.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t('agent_modal.key_points')}
          </div>
          {opinion.key_points.map((p, i) => (
            <div key={i} style={{ fontSize: 11, color: 'var(--text-secondary)', padding: '2px 0', paddingLeft: 12 }}>
              • {p}
            </div>
          ))}
        </div>
      )}

      {opinion.risk_factors && opinion.risk_factors.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-red)', marginBottom: 4 }}>
            {t('agent_modal.risk_factors')}
          </div>
          {opinion.risk_factors.map((r, i) => (
            <div key={i} style={{ fontSize: 11, color: 'var(--text-secondary)', padding: '2px 0', paddingLeft: 12 }}>
              ⚠️ {r}
            </div>
          ))}
        </div>
      )}

      {opinion.data_evidence && Object.keys(opinion.data_evidence).length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {t('agent_modal.data_evidence')}
          </div>
          <pre style={{
            fontSize: 10, color: 'var(--text-muted)', background: 'var(--bg-input)',
            borderRadius: 8, padding: 10, overflow: 'auto', maxHeight: 140,
            border: '1px solid var(--border)', lineHeight: 1.5,
          }}>
            {JSON.stringify(opinion.data_evidence, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
