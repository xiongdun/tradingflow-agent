// frontend/src/main.tsx
// React 应用入口 — 挂载根组件到 DOM

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// 渲染根组件，StrictMode 用于开发环境检测潜在问题
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
