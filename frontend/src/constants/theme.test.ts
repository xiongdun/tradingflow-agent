import { describe, it, expect } from 'vitest';
import { AGENT_COLORS, MARKET_COLORS } from './theme';

describe('AGENT_COLORS', () => {
  it('should have colors for all agent roles', () => {
    const expectedRoles = [
      'fundamental',
      'technical',
      'sentiment',
      'news',
      'macro',
      'hot_money',
      'quant',
      'risk',
      'sector_rotation',
      'summarizer',
    ];

    for (const role of expectedRoles) {
      expect(AGENT_COLORS[role]).toBeDefined();
      expect(typeof AGENT_COLORS[role]).toBe('string');
      expect(AGENT_COLORS[role]).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });

  it('should have unique colors for each role', () => {
    const colors = Object.values(AGENT_COLORS);
    const uniqueColors = new Set(colors);
    expect(uniqueColors.size).toBe(colors.length);
  });

  it('should include summarizer color', () => {
    expect(AGENT_COLORS.summarizer).toBeDefined();
  });
});

describe('MARKET_COLORS', () => {
  it('should have colors for all markets', () => {
    expect(MARKET_COLORS.a_share).toBeDefined();
    expect(MARKET_COLORS.us_stock).toBeDefined();
    expect(MARKET_COLORS.h_stock).toBeDefined();
  });

  it('should have valid hex colors', () => {
    for (const color of Object.values(MARKET_COLORS)) {
      expect(color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });
});
