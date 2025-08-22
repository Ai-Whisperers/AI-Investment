/**
 * Tests for diagnostics API service
 * Single responsibility: Test API communication
 */

import { diagnosticsService } from '@/app/services/api/diagnostics'
import { mockDiagnostics, createMockPriceData } from '../../utils/mock-data'
import { createMockFetch } from '../../utils/mock-api'

describe('DiagnosticsService', () => {
  let originalFetch: typeof global.fetch

  beforeEach(() => {
    originalFetch = global.fetch
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  describe('getSystemHealth', () => {
    it('should fetch system health data', async () => {
      global.fetch = createMockFetch({
        getSystemHealth: mockDiagnostics,
      }) as any

      const result = await diagnosticsService.getDatabaseStatus()

      expect(result).toEqual(mockDiagnostics)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/diagnostics/health'),
        expect.any(Object)
      )
    })

    it('should handle API errors gracefully', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'))

      await expect(diagnosticsService.getDatabaseStatus()).rejects.toThrow('Network error')
    })
  })

  describe('getCacheStatus', () => {
    it('should fetch cache status', async () => {
      const mockCacheStatus = {
        enabled: true,
        hit_rate: 0.85,
        memory_usage_mb: 128,
      }

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockCacheStatus),
      })

      const result = await diagnosticsService.getCacheStatus()

      expect(result).toEqual(mockCacheStatus)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/diagnostics/cache-status'),
        expect.any(Object)
      )
    })
  })

  describe('getDatabaseStatus', () => {
    it('should fetch database status', async () => {
      const mockDbStatus = {
        status: 'healthy',
        connection_count: 5,
        response_time_ms: 25,
      }

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockDbStatus),
      })

      const result = await diagnosticsService.getDatabaseStatus()

      expect(result).toEqual(mockDbStatus)
    })

    it('should handle non-OK responses', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      })

      await expect(diagnosticsService.getDatabaseStatus()).rejects.toThrow()
    })
  })
})