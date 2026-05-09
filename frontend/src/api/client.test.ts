import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import apiClient from './client';

describe('apiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should have correct baseURL', () => {
    expect(apiClient.defaults.baseURL).toBe('/api');
  });

  it('should have correct headers', () => {
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('should handle GET request', async () => {
    const mockData = { data: 'test' };
    vi.spyOn(axios, 'get').mockResolvedValue({ data: mockData });

    const response = await apiClient.get('/test');
    expect(response.data).toEqual(mockData);
  });

  it('should handle POST request', async () => {
    const mockData = { result: 'success' };
    const payload = { symbol: '600519' };
    vi.spyOn(axios, 'post').mockResolvedValue({ data: mockData });

    const response = await apiClient.post('/analyze', payload);
    expect(response.data).toEqual(mockData);
  });

  it('should handle request error', async () => {
    const error = new Error('Network Error');
    vi.spyOn(axios, 'get').mockRejectedValue(error);

    await expect(apiClient.get('/test')).rejects.toThrow('Network Error');
  });

  it('should handle 404 error', async () => {
    const error = new Error('Request failed with status code 404');
    vi.spyOn(axios, 'get').mockRejectedValue(error);

    await expect(apiClient.get('/nonexistent')).rejects.toThrow('404');
  });
});
