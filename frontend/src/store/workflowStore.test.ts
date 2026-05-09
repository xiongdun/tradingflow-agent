import { describe, it, expect, beforeEach } from 'vitest';
import { useWorkflowStore } from './workflowStore';

describe('workflowStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useWorkflowStore.setState({
      nodes: [],
      edges: [],
      selectedNode: null,
      selectedEdge: null,
      analysisProgress: {},
      opinions: [],
      finalReport: null,
      isAnalyzing: false,
      analysisError: null,
      symbol: '',
      market: 'a_share',
      activeTab: 'workflow',
      theme: 'system',
      colorScheme: 'cn',
    });
  });

  it('should have correct initial state', () => {
    const state = useWorkflowStore.getState();
    expect(state.nodes).toEqual([]);
    expect(state.edges).toEqual([]);
    expect(state.isAnalyzing).toBe(false);
    expect(state.symbol).toBe('');
    expect(state.market).toBe('a_share');
    expect(state.activeTab).toBe('workflow');
    expect(state.theme).toBe('system');
    expect(state.colorScheme).toBe('cn');
  });

  it('should set nodes', () => {
    const newNodes = [{ id: '1', type: 'agent', position: { x: 0, y: 0 }, data: {} }];
    useWorkflowStore.getState().setNodes(newNodes);
    expect(useWorkflowStore.getState().nodes).toEqual(newNodes);
  });

  it('should set edges', () => {
    const newEdges = [{ id: 'e1', source: '1', target: '2' }];
    useWorkflowStore.getState().setEdges(newEdges);
    expect(useWorkflowStore.getState().edges).toEqual(newEdges);
  });

  it('should set selected node', () => {
    useWorkflowStore.getState().setSelectedNode('node-1');
    expect(useWorkflowStore.getState().selectedNode).toBe('node-1');
  });

  it('should set selected edge', () => {
    useWorkflowStore.getState().setSelectedEdge('edge-1');
    expect(useWorkflowStore.getState().selectedEdge).toBe('edge-1');
  });

  it('should set symbol and market', () => {
    useWorkflowStore.getState().setSymbol('600519');
    useWorkflowStore.getState().setMarket('a_share');
    expect(useWorkflowStore.getState().symbol).toBe('600519');
    expect(useWorkflowStore.getState().market).toBe('a_share');
  });

  it('should set active tab', () => {
    useWorkflowStore.getState().setActiveTab('report');
    expect(useWorkflowStore.getState().activeTab).toBe('report');
  });

  it('should set theme', () => {
    useWorkflowStore.getState().setTheme('dark');
    expect(useWorkflowStore.getState().theme).toBe('dark');
  });

  it('should set color scheme', () => {
    useWorkflowStore.getState().setColorScheme('international');
    expect(useWorkflowStore.getState().colorScheme).toBe('international');
  });

  it('should set analyzing state', () => {
    useWorkflowStore.getState().setIsAnalyzing(true);
    expect(useWorkflowStore.getState().isAnalyzing).toBe(true);
  });

  it('should set analysis error', () => {
    useWorkflowStore.getState().setAnalysisError('Network error');
    expect(useWorkflowStore.getState().analysisError).toBe('Network error');
  });

  it('should update analysis progress', () => {
    useWorkflowStore.getState().setAnalysisProgress({ agent: 'fundamental', status: 'running' });
    expect(useWorkflowStore.getState().analysisProgress).toEqual({ agent: 'fundamental', status: 'running' });
  });

  it('should set opinions', () => {
    const opinions = [{ agent_role: 'fundamental', stance: 'bullish' }];
    useWorkflowStore.getState().setOpinions(opinions);
    expect(useWorkflowStore.getState().opinions).toEqual(opinions);
  });

  it('should set final report', () => {
    const report = { overall_stance: 'bullish', confidence: 0.85 };
    useWorkflowStore.getState().setFinalReport(report);
    expect(useWorkflowStore.getState().finalReport).toEqual(report);
  });
});
