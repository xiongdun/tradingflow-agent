// frontend/src/hooks/useWebSocket.ts
// WebSocket Hook — 管理与后端 /ws/analyze 的实时连接，处理分析进度和结果推送

import { useCallback, useRef } from 'react';
import { useWorkflowStore } from '../store/workflowStore';
import type { WSMessage } from '../types';

const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000; // 1s, doubles each attempt

/**
 * useWebSocket — 管理 WebSocket 连接的自定义 Hook
 * 提供连接、发送分析请求、断开连接三个方法
 * 消息协议：status（状态变更）、opinion（分析师意见）、report（最终报告）、error（错误）
 * 支持自动重连（指数退避，最多 5 次）
 */
export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);  // WebSocket 实例引用
  const store = useWorkflowStore();               // 全局状态管理
  const reconnectAttempts = useRef(0);            // 重连尝试次数
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null); // 重连定时器
  const intentionallyClosed = useRef(false);      // 是否主动关闭

  /** 建立 WebSocket 连接，注册消息处理器 */
  const connect = useCallback(() => {
    // 已达最大重连次数，停止
    if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) return null;

    // 清除待执行的重连定时器
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    // 根据页面协议自动选择 ws 或 wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/analyze`);
    wsRef.current = ws;

    // 连接成功时重置重连计数
    ws.onopen = () => {
      reconnectAttempts.current = 0;
      store.addProgress('✅ WebSocket 已连接');
    };

    // 处理后端推送的消息
    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);
      switch (msg.type) {
        case 'status':
          // 状态变更：started（工作流启动）、running（分析中）、completed（完成）
          if (msg.status === 'started') {
            store.addProgress(`🚀 工作流开始: ${msg.workflow}`);
            // 从 workflow 定义中提取 agents 列表，让 AgentNodes 开始脉冲
            const wfAgents: string[] = (msg as any).workflow?.agents?.map((a: any) => a.role) || [];
            if (wfAgents.length > 0) store.setAnalyzingAgents(wfAgents);
          }
          if (msg.status === 'running') {
            store.setAnalyzingAgents(msg.agents || []);
            store.addProgress(`⏳ 分析中: ${msg.agents?.join(', ')}`);
          }
          if (msg.status === 'completed') {
            store.setAnalyzingAgents([]);
            store.setAnalyzing(false);
            store.addProgress('✅ 分析完成');
          }
          break;
        case 'agent_status': {
          // 单个 Agent 的执行状态更新
          const role = msg.agent_role || '';
          if (msg.status === 'running') {
            store.setAgentProgress(role, { status: 'running', messages: [`⏳ ${msg.agent_name || role} 开始分析...`] });
          } else if (msg.status === 'skill_done') {
            const curr = store.agentProgressMap[role] || { status: 'running', messages: [] };
            store.setAgentProgress(role, { messages: [...curr.messages, `✅ 技能完成: ${msg.skill || ''}`] });
          } else if (msg.status === 'done') {
            store.setAgentProgress(role, { status: 'done' });
          } else if (msg.status === 'error') {
            store.setAgentProgress(role, { status: 'error', messages: [`❌ 错误: ${msg.message}`] });
          }
          break;
        }
        case 'opinion': {
          // 收到单个分析师的意见，添加到全局状态并显示进度，同时标记该 Agent 完成
          store.addOpinion(msg.data as any);
          const op = msg.data as any;
          store.removeAnalyzingAgent(op.agent_role);
          store.setAgentProgress(op.agent_role, { status: 'done', opinion: op });
          store.addProgress(`📊 ${op.agent_name}: ${op.stance} (${(op.confidence * 100).toFixed(0)}%)`);
          break;
        }
        case 'report':
          // 收到最终报告（含 Markdown 格式），自动切换到结果标签页
          store.setFinalReport(msg.data as any, msg.markdown || '');
          window.dispatchEvent(new Event('switch-to-report'));
          break;
        case 'error':
          // 分析出错，停止分析状态
          store.addProgress(`❌ 错误: ${msg.message}`);
          store.setAnalyzing(false);
          break;
      }
    };

    // 连接关闭时 — 主动关闭则不重连，否则指数退避重连
    ws.onclose = () => {
      wsRef.current = null;
      if (!intentionallyClosed.current && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current);
        reconnectAttempts.current++;
        store.addProgress(`连接断开，${delay / 1000}秒后重连 (第${reconnectAttempts.current}次)...`);
        reconnectTimer.current = setTimeout(() => connect(), delay);
      } else if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
        store.addProgress('⚠️ WebSocket 连接失败，请检查后端服务是否启动');
      }
    };

    // 连接错误时触发关闭（由 onclose 处理重连）
    ws.onerror = () => { ws.close(); };

    return ws;
  }, [store]);

  /**
   * 发送分析请求 — 重置状态后通过 WebSocket 发送股票代码和工作流配置
   * @param symbol 股票代码
   * @param market 市场类型
   * @param workflow 工作流模板名称
   * @param agents 自定义 Agent 角色列表（可选，覆盖模板）
   * @param agentInfos Agent 详细信息列表（含名称，用于自定义 Agent）
   */
  const sendAnalysis = useCallback((symbol: string, market: string, workflow: string, agents?: string[], agentInfos?: { role: string; name: string }[]) => {
    intentionallyClosed.current = false; // 允许重连
    store.resetAnalysis();   // 清除上次分析结果
    store.setAnalyzing(true); // 标记为分析中
    reconnectAttempts.current = 0; // 重置重连计数
    const ws = wsRef.current || connect();  // 复用已有连接或新建
    if (!ws) {
      store.setAnalyzing(false);
      store.addProgress('⚠️ 无法建立 WebSocket 连接，请检查后端服务是否启动');
      return;
    }
    const payload = { symbol, market, workflow, agents, agent_infos: agentInfos };
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
    } else {
      // 连接尚未就绪，等待 open 后发送
      const onOpenHandler = () => {
        ws.removeEventListener('open', onOpenHandler);
        ws.send(JSON.stringify(payload));
      };
      ws.addEventListener('open', onOpenHandler);
    }
  }, [store, connect]);

  /** 断开 WebSocket 连接（主动关闭，不触发自动重连） */
  const disconnect = useCallback(() => {
    intentionallyClosed.current = true;
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { connect, sendAnalysis, disconnect };
}
