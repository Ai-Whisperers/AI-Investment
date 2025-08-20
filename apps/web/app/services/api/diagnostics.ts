// Diagnostics API Service

import { ApiService } from './base';

export interface TableInfo {
  count: number;
  status: 'OK' | 'EMPTY' | 'ERROR';
  earliest_date?: string;
  latest_date?: string;
  error?: string;
}

export interface DatabaseStatus {
  timestamp: string;
  connected?: boolean;
  database_name?: string;
  tables: {
    users: TableInfo;
    assets: TableInfo;
    prices: TableInfo;
    index_values: TableInfo;
    allocations: TableInfo;
  };
  simulation_ready: boolean;
  message: string;
}

export interface RefreshStatus {
  assets: {
    count: number;
    symbols: string[];
    has_benchmark: boolean;
  };
  prices: {
    latest_date: string | null;
    days_old: number | null;
    needs_update: boolean;
  };
  recommendation: string;
  last_attempt?: string;
  last_successful?: string;
  last_status?: string;
  last_error?: string;
  assets_updated?: number;
  prices_added?: number;
  data_freshness?: {
    hours: number;
    status: 'fresh' | 'stale' | 'outdated';
  };
}

export interface CacheStatus {
  timestamp: string;
  status: 'connected' | 'disconnected' | 'error';
  message: string;
  connected?: boolean;
  total_requests?: number;
  hits?: number;
  misses?: number;
  keys?: number;
  memory_usage?: string;
  cache_by_type?: Record<string, number>;
  stats?: {
    total_entries: number;
    memory_usage?: string;
    memory_used?: string;
    hit_rate?: number;
    miss_rate?: number;
    keys_by_prefix?: Record<string, number>;
    prefixes?: Record<string, number>;
  };
  error?: string;
}

export interface CacheInvalidateResponse {
  timestamp: string;
  status: 'success' | 'error';
  invalidated_count: number;
  message: string;
  error?: string;
}

export interface TestRefreshResult {
  timestamp: string;
  steps: Array<{
    step: string;
    status: 'starting' | 'success' | 'failed' | 'skipped';
    [key: string]: any;
  }>;
  overall_status: 'SUCCESS' | 'PARTIAL_SUCCESS' | 'FAILED';
  error?: string;
  traceback?: string;
}

export interface RecalculateResult {
  timestamp: string;
  status: 'starting' | 'success' | 'error';
  before?: {
    index_values: number;
    allocations: number;
  };
  after?: {
    index_values: number;
    allocations: number;
  };
  sample_recent_values?: Array<{
    date: string;
    value: number;
  }>;
  error?: string;
  traceback?: string;
}

export class DiagnosticsService extends ApiService {
  async getDatabaseStatus(): Promise<DatabaseStatus> {
    return this.get<DatabaseStatus>('/api/v1/diagnostics/database-status');
  }

  async getRefreshStatus(): Promise<RefreshStatus> {
    return this.get<RefreshStatus>('/api/v1/diagnostics/refresh-status');
  }

  async getCacheStatus(): Promise<CacheStatus> {
    return this.get<CacheStatus>('/api/v1/diagnostics/cache-status');
  }

  async invalidateCache(pattern: string = '*'): Promise<CacheInvalidateResponse> {
    return this.post<CacheInvalidateResponse>('/api/v1/diagnostics/cache-invalidate', { pattern });
  }

  async testRefresh(): Promise<TestRefreshResult> {
    return this.post<TestRefreshResult>('/api/v1/diagnostics/test-refresh');
  }

  async recalculateIndex(): Promise<RecalculateResult> {
    return this.post<RecalculateResult>('/api/v1/diagnostics/recalculate-index');
  }
}

export const diagnosticsService = new DiagnosticsService();