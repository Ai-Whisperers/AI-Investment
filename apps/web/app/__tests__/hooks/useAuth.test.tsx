/**
 * Tests for useAuth hook
 * Single responsibility: Test authentication logic
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useAuth } from '@/app/core/presentation/contexts/AuthContext'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the auth service
jest.mock('@/services/api/auth', () => ({
  authService: {
    login: jest.fn(),
    logout: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}))

describe('useAuth', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  describe('Initial State', () => {
    it('should return initial auth state', () => {
      const { result } = renderHook(() => useAuth(), { wrapper })

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(result.current.isLoading).toBe(true)
    })
  })

  describe('Login', () => {
    it('should handle successful login', async () => {
      const mockUser = { id: 1, email: 'test@example.com' }
      const authService = require('@/services/api/auth').authService
      authService.login.mockResolvedValue({
        access_token: 'mock-token',
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' })
      })

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true)
        expect(result.current.user).toEqual(mockUser)
      })
    })

    it('should handle login failure', async () => {
      const authService = require('@/services/api/auth').authService
      authService.login.mockRejectedValue(new Error('Invalid credentials'))

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({ email: 'test@example.com', password: 'wrong-password' })
        } catch (error) {
          expect(error).toEqual(new Error('Invalid credentials'))
        }
      })

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })
  })

  describe('Logout', () => {
    it('should clear auth state on logout', async () => {
      const authService = require('@/services/api/auth').authService
      authService.logout.mockResolvedValue(undefined)

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Set initial authenticated state
      act(() => {
        result.current.user = { 
          id: '1', 
          email: 'test@example.com',
          role: 'user' as any,
          createdAt: new Date(),
          updatedAt: new Date()
        }
        result.current.isAuthenticated = true
      })

      await act(async () => {
        await result.current.logout()
      })

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })
  })
})