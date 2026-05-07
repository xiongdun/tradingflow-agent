// frontend/src/hooks/useTheme.ts
// 主题切换 Hook — 管理深色/浅色主题，通过 CSS 变量和 data-theme 属性切换

import { useState, useEffect, useCallback } from 'react';

export type Theme = 'dark' | 'light';

const STORAGE_KEY = 'tradingflow-theme';

/**
 * useTheme — 主题切换 Hook
 * 读取 localStorage 持久化偏好，默认深色主题。
 * 切换时在 <html> 上设置 data-theme 属性，CSS 变量自动生效。
 */
export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return (saved === 'light' || saved === 'dark') ? saved : 'dark';
  });

  // 同步 data-theme 属性到 DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggle = useCallback(() => {
    setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  return { theme, toggle };
}
