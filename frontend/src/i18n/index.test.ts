import { describe, it, expect } from 'vitest';
import i18n from './index';

describe('i18n', () => {
  it('should export i18n instance', () => {
    expect(i18n).toBeDefined();
  });

  it('should have t function', () => {
    expect(typeof i18n.t).toBe('function');
  });

  it('should translate simple key', () => {
    const result = i18n.t('report_title');
    expect(result).toBeDefined();
    expect(typeof result).toBe('string');
  });

  it('should handle interpolation', () => {
    const result = i18n.t('report_title', { stock: '600519', market: 'a_share' });
    expect(result).toContain('600519');
    expect(result).toContain('a_share');
  });

  it('should return key for missing translation', () => {
    const result = i18n.t('nonexistent_key_xyz');
    expect(result).toBe('nonexistent_key_xyz');
  });
});
