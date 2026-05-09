// frontend/src/components/common/Toast.tsx
// 全局错误/消息 Toast 组件 — 通过自定义事件驱动，支持自动消失

import { useState, useEffect, useCallback } from 'react';

export interface ToastMessage {
  id: number;
  text: string;
  type: 'error' | 'warning' | 'success' | 'info';
  duration?: number;
}

const DEFAULT_DURATION = 4000;

let _nextId = 0;

/** 全局触发 Toast 消息（可在任何地方调用） */
export function showToast(text: string, type: ToastMessage['type'] = 'error', duration = DEFAULT_DURATION) {
  const event = new CustomEvent<ToastMessage>('toast:show', {
    detail: { id: _nextId++, text, type, duration },
  });
  window.dispatchEvent(event);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  useEffect(() => {
    const handler = (e: Event) => {
      const msg = (e as CustomEvent<ToastMessage>).detail;
      setToasts((prev) => [...prev, msg]);
      setTimeout(() => dismiss(msg.id), msg.duration || DEFAULT_DURATION);
    };
    window.addEventListener('toast:show', handler);
    return () => window.removeEventListener('toast:show', handler);
  }, [dismiss]);

  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', top: 16, right: 16, zIndex: 9999,
      display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 400,
    }}>
      {toasts.map((t) => {
        const bg = t.type === 'error' ? 'rgba(239,68,68,0.95)'
          : t.type === 'warning' ? 'rgba(245,158,11,0.95)'
          : t.type === 'success' ? 'rgba(34,197,94,0.95)'
          : 'rgba(99,102,241,0.95)';
        return (
          <div
            key={t.id}
            onClick={() => dismiss(t.id)}
            style={{
              background: bg, color: '#fff', padding: '10px 16px',
              borderRadius: 10, fontSize: 13, fontWeight: 500,
              cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
              animation: 'toastIn 0.3s ease-out',
              backdropFilter: 'blur(12px)',
            }}
          >
            {t.text}
          </div>
        );
      })}
      <style>{`
        @keyframes toastIn {
          from { opacity: 0; transform: translateX(40px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
