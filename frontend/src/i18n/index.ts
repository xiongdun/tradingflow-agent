// frontend/src/i18n/index.ts
// 轻量 i18n — t() 翻译函数 + 从后端加载语言配置

import zh from './zh.json';
import en from './en.json';

const locales: Record<string, Record<string, string>> = { zh, en };
let currentLang = 'zh';
let dict: Record<string, string> = zh;

/** 设置当前语言 */
export function setLocale(lang: string) {
  currentLang = lang;
  dict = locales[lang] || zh;
}

/** 获取当前语言 */
export function getLocale(): string {
  return currentLang;
}

/** 翻译函数 — 根据 key 返回对应语言文本，未找到则返回 key 本身 */
export function t(key: string): string {
  return dict[key] || key;
}

/** 从后端 /api/config 加载语言配置并应用 */
export async function loadLocale(): Promise<void> {
  try {
    const resp = await fetch('/api/config');
    const config = await resp.json();
    if (config.language) {
      setLocale(config.language);
    }
  } catch {
    // 加载失败时使用默认中文
  }
}
