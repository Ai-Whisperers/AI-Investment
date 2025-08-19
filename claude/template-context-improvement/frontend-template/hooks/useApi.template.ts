// useApi.ts - API Hook template (Keep under 150 lines)

/**
 * AI NOTE: This is a template for a custom API hook.
 * Handles loading states, errors, and caching.
 * Keep hooks focused and under 150 lines.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { AxiosError } from 'axios';
import { api } from '@/services/api/client';

interface UseApiOptions {
  immediate?: boolean;  // Execute immediately on mount
  cache?: boolean;      // Cache results
  cacheTime?: number;   // Cache duration in ms
  retries?: number;     // Number of retries on failure
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (params?: any) => Promise<T | null>;
  reset: () => void;
}

// Simple in-memory cache
const cache = new Map<string, { data: any; timestamp: number }>();

/**
 * Generic API hook for data fetching
 * @param endpoint - API endpoint
 * @param options - Configuration options
 */
export function useApi<T = any>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const {
    immediate = true,
    cache: useCache = false,
    cacheTime = 5 * 60 * 1000, // 5 minutes default
    retries = 0,
    onSuccess,
    onError
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  // Use ref to track if component is mounted
  const isMounted = useRef(true);
  const abortController = useRef<AbortController>();

  /**
   * Check if cached data is still valid
   */
  const getCachedData = useCallback((key: string): T | null => {
    if (!useCache) return null;
    
    const cached = cache.get(key);
    if (!cached) return null;
    
    const isExpired = Date.now() - cached.timestamp > cacheTime;
    if (isExpired) {
      cache.delete(key);
      return null;
    }
    
    return cached.data as T;
  }, [useCache, cacheTime]);

  /**
   * Set data in cache
   */
  const setCachedData = useCallback((key: string, data: T) => {
    if (!useCache) return;
    
    cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }, [useCache]);

  /**
   * Execute API call
   */
  const execute = useCallback(async (params?: any): Promise<T | null> => {
    // Cancel previous request if exists
    if (abortController.current) {
      abortController.current.abort();
    }

    // Create cache key
    const cacheKey = `${endpoint}:${JSON.stringify(params || {})}`;
    
    // Check cache first
    const cachedData = getCachedData(cacheKey);
    if (cachedData) {
      setData(cachedData);
      return cachedData;
    }

    // Create new abort controller
    abortController.current = new AbortController();
    
    setLoading(true);
    setError(null);

    let attemptCount = 0;
    const maxAttempts = retries + 1;

    while (attemptCount < maxAttempts) {
      try {
        const response = await api.get<T>(endpoint, {
          params,
          signal: abortController.current.signal
        });

        const responseData = response.data;

        // Only update state if component is still mounted
        if (isMounted.current) {
          setData(responseData);
          setCachedData(cacheKey, responseData);
          onSuccess?.(responseData);
        }

        return responseData;
      } catch (err) {
        attemptCount++;
        
        // Don't retry on abort
        if ((err as AxiosError).code === 'ERR_CANCELED') {
          break;
        }

        // If this was the last attempt, set error
        if (attemptCount >= maxAttempts && isMounted.current) {
          const error = err as Error;
          setError(error);
          onError?.(error);
          return null;
        }

        // Wait before retrying (exponential backoff)
        if (attemptCount < maxAttempts) {
          await new Promise(resolve => 
            setTimeout(resolve, Math.pow(2, attemptCount) * 1000)
          );
        }
      } finally {
        if (isMounted.current && attemptCount >= maxAttempts) {
          setLoading(false);
        }
      }
    }

    return null;
  }, [endpoint, retries, getCachedData, setCachedData, onSuccess, onError]);

  /**
   * Reset hook state
   */
  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  /**
   * Execute on mount if immediate is true
   */
  useEffect(() => {
    if (immediate) {
      execute();
    }

    return () => {
      isMounted.current = false;
      abortController.current?.abort();
    };
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset
  };
}

// Specialized hooks built on useApi
export const useUser = (userId: string) => 
  useApi<User>(`/users/${userId}`, { cache: true });

export const useUsers = () => 
  useApi<User[]>('/users', { cache: true, cacheTime: 60000 });

export const useProducts = (filters?: ProductFilters) => 
  useApi<Product[]>('/products', { cache: true });

// Types (normally in separate file)
interface User {
  id: string;
  name: string;
  email: string;
}

interface Product {
  id: string;
  name: string;
  price: number;
}

interface ProductFilters {
  category?: string;
  minPrice?: number;
  maxPrice?: number;
}