/**
 * Mock API responses for testing
 * Single responsibility: API mocking
 */

export const mockApiResponses = {
  // Auth endpoints
  login: {
    access_token: 'mock-jwt-token',
    token_type: 'bearer',
    user: {
      id: 1,
      email: 'test@example.com',
    },
  },
  
  // Portfolio endpoints
  getPortfolio: {
    id: 1,
    name: 'Test Portfolio',
    total_value: 100000,
    returns: 0.15,
    positions: [],
  },
  
  // Diagnostics endpoints
  getSystemHealth: {
    status: 'healthy',
    checks: {
      database: 'ok',
      cache: 'ok',
      api: 'ok',
    },
  },
}

/**
 * Create mock fetch function for testing
 */
export function createMockFetch(responses: Record<string, any> = mockApiResponses) {
  return jest.fn((url: string) => {
    // Parse the URL to determine which response to return
    const path = new URL(url).pathname
    
    // Match path to response
    let response = null
    if (path.includes('/auth/login')) {
      response = responses.login
    } else if (path.includes('/portfolio')) {
      response = responses.getPortfolio
    } else if (path.includes('/diagnostics')) {
      response = responses.getSystemHealth
    }
    
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(response || {}),
      status: 200,
    })
  })
}