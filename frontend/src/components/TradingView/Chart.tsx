// frontend/src/components/TradingView/Chart.tsx
// TradingView K 线图组件 — 使用 Lightweight Charts 渲染蜡烛图和分析师买卖信号标记

import { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, createSeriesMarkers, type IChartApi, type ISeriesApi, type ISeriesMarkersPluginApi } from 'lightweight-charts';
import { useWorkflowStore } from '../../store/workflowStore';
import { getKline, getMarkers, getConfig } from '../../api/client';

/** K 线数据点 */
interface BarData { time: string; open: number; high: number; low: number; close: number; volume?: number; }
/** 图表标记（买卖信号箭头） */
interface Marker { time?: string; position: string; color: string; shape: string; text: string; tooltip?: string; }

/**
 * TradingViewChart — K 线图组件
 * 功能：加载 K 线数据、渲染蜡烛图、叠加分析师买卖信号标记
 * @param height 图表高度（默认 400px）
 */
export function TradingViewChart({ height = 400 }: { height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);       // 图表容器 DOM 引用
  const chartRef = useRef<IChartApi | null>(null);         // 图表实例引用
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);  // 蜡烛图系列引用
  const markersPluginRef = useRef<ISeriesMarkersPluginApi<unknown> | null>(null);  // 标记插件引用
  const [bars, setBars] = useState<BarData[]>([]);         // K 线数据
  const [markers, setMarkers] = useState<Marker[]>([]);    // 买卖信号标记
  const [colorScheme, setColorScheme] = useState<'cn' | 'international'>('cn');  // 涨跌颜色方案
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');  // 主题（用于图表重绘）
  const { selectedSymbol, selectedMarket, opinions, finalReport } = useWorkflowStore();

  // 监听主题变化
  useEffect(() => {
    const current = document.documentElement.getAttribute('data-theme') as 'dark' | 'light' || 'dark';
    setTheme(current);
    const observer = new MutationObserver(() => {
      const t = document.documentElement.getAttribute('data-theme') as 'dark' | 'light' || 'dark';
      setTheme(t);
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  // 获取颜色配置
  useEffect(() => {
    getConfig()
      .then((config) => {
        if (config.color_scheme === 'international') {
          setColorScheme('international');
        }
      })
      .catch(() => {});
  }, []);

  // 当股票代码或市场变化时，拉取 K 线数据
  useEffect(() => {
    if (!selectedSymbol) return;
    setBars([]);
    setMarkers([]);
    getKline(selectedSymbol, selectedMarket, 'daily', 120)
      .then((res) => setBars(res.bars || []))
      .catch(() => setBars([]));
  }, [selectedSymbol, selectedMarket]);

  // 当分析师意见更新时，拉取图表标记数据
  useEffect(() => {
    if (!selectedSymbol || opinions.length === 0) return;
    getMarkers(selectedSymbol, selectedMarket, opinions)
      .then((res) => {
        // 将标记时间设为最后一根 K 线的时间（标记显示在最新位置）
        if (bars.length > 0) {
          const lastTime = bars[bars.length - 1].time;
          const enrichedMarkers = res.markers.map((m: Marker) => ({ ...m, time: lastTime }));
          setMarkers(enrichedMarkers);
        }
      })
      .catch(() => {});
  }, [opinions, selectedSymbol, selectedMarket, bars]);

  // 创建/重建图表实例（仅依赖 height，主题更新由单独的 effect 处理）
  useEffect(() => {
    if (!containerRef.current) return;

    // 移除旧图表（防御已 dispose 的情况）
    if (chartRef.current) {
      try { chartRef.current.remove(); } catch {}
      chartRef.current = null;
      seriesRef.current = null;
    }

    // 读取 CSS 变量的实际值（lightweight-charts 需要真实颜色值，不支持 CSS 变量）
    const cs = getComputedStyle(document.documentElement);
    const bg = cs.getPropertyValue('--bg').trim() || '#0f0f13';
    const border = cs.getPropertyValue('--border').trim() || '#27272a';

    // 创建新图表，配置主题
    const chart = createChart(containerRef.current, {
      layout: { background: { color: bg }, textColor: '#d1d5db' },
      grid: { vertLines: { color: border }, horzLines: { color: border } },
      width: containerRef.current.clientWidth,
      height,
      timeScale: { timeVisible: false, borderColor: border },
      rightPriceScale: { borderColor: border },
      crosshair: { mode: 0 },
    });

    // 添加蜡烛图系列，配置涨跌颜色（根据颜色方案）
    const upColor = colorScheme === 'cn' ? '#ef4444' : '#22c55e';    // 中国红涨，国际绿涨
    const downColor = colorScheme === 'cn' ? '#22c55e' : '#ef4444';  // 中国绿跌，国际红跌
    const series = chart.addSeries(CandlestickSeries, {
      upColor, downColor,
      borderUpColor: upColor, borderDownColor: downColor,
      wickUpColor: upColor, wickDownColor: downColor,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    // 创建标记插件（用于显示买卖信号）
    const markersPlugin = createSeriesMarkers(series, []);
    markersPluginRef.current = markersPlugin;

    // 窗口大小变化时自动调整图表宽度
    const resize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    window.addEventListener('resize', resize);
    return () => { window.removeEventListener('resize', resize); try { chart.remove(); } catch {} };
  }, [height]);

  // 主题/颜色方案热更新（通过 applyOptions 避免重建图表）
  useEffect(() => {
    if (!chartRef.current || !seriesRef.current) return;
    const cs = getComputedStyle(document.documentElement);
    const bg = cs.getPropertyValue('--bg').trim() || '#0f0f13';
    const border = cs.getPropertyValue('--border').trim() || '#27272a';

    chartRef.current.applyOptions({
      layout: { background: { color: bg }, textColor: '#d1d5db' },
      grid: { vertLines: { color: border }, horzLines: { color: border } },
      timeScale: { borderColor: border },
      rightPriceScale: { borderColor: border },
    });

    const upColor = colorScheme === 'cn' ? '#ef4444' : '#22c55e';
    const downColor = colorScheme === 'cn' ? '#22c55e' : '#ef4444';
    seriesRef.current.applyOptions({
      upColor, downColor,
      borderUpColor: upColor, borderDownColor: downColor,
      wickUpColor: upColor, wickDownColor: downColor,
    });
  }, [colorScheme, theme]);

  // K 线数据更新时渲染到图表
  useEffect(() => {
    if (!seriesRef.current || bars.length === 0) return;
    seriesRef.current.setData(bars);
    chartRef.current?.timeScale().fitContent();
  }, [bars]);

  // 标记数据更新时渲染买卖信号
  useEffect(() => {
    if (!markersPluginRef.current || markers.length === 0) return;
    markersPluginRef.current.setMarkers(
      markers.map((m) => ({
        time: m.time as any,
        position: m.position as any,
        color: m.color,
        shape: m.shape as any,
        text: m.text,
      }))
    );
  }, [markers]);

  return (
    <div style={{ position: 'relative' }}>
      {/* 左上角：股票代码和最新价标签 */}
      {selectedSymbol && (
        <div style={{
          position: 'absolute', top: 8, left: 12, zIndex: 10,
          background: 'var(--bg-panel)', borderRadius: 6, padding: '4px 12px', opacity: 0.9,
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--text)' }}>{selectedSymbol}</span>
          {/* 市场国旗标识 */}
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {selectedMarket === 'a_share' ? '🇨🇳' : selectedMarket === 'us_stock' ? '🇺🇸' : '🇭🇰'}
          </span>
          {/* 最新收盘价（根据颜色方案） */}
          {bars.length > 0 && (
            <span style={{ fontSize: 13, color: bars[bars.length - 1].close >= bars[bars.length - 1].open ? (colorScheme === 'cn' ? '#ef4444' : '#22c55e') : (colorScheme === 'cn' ? '#22c55e' : '#ef4444') }}>
              ¥{bars[bars.length - 1].close.toFixed(2)}
            </span>
          )}
        </div>
      )}

      {/* 右上角：买卖信号图例 */}
      {markers.length > 0 && (
        <div style={{
          position: 'absolute', top: 8, right: 12, zIndex: 10,
          background: 'var(--bg-panel)', borderRadius: 6, padding: '4px 10px', opacity: 0.9,
          display: 'flex', gap: 10, fontSize: 11,
        }}>
          <span><span style={{ color: '#22c55e' }}>▲</span> 看多</span>
          <span><span style={{ color: '#ef4444' }}>▼</span> 看空</span>
        </div>
      )}

      {/* 图表容器 */}
      <div
        ref={containerRef}
        style={{ width: '100%', height, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}
      />

      {/* 未选择股票时的占位提示 */}
      {!selectedSymbol && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'var(--bg)', color: 'var(--text-muted)', fontSize: 14, borderRadius: 8,
        }}>
          输入股票代码后显示K线图
        </div>
      )}
    </div>
  );
}
