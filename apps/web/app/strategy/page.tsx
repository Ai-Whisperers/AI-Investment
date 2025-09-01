'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { strategyService } from '../services/api/strategy';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';

interface StrategyConfig {
  min_market_cap?: number;
  max_assets?: number;
  rebalance_frequency?: string;
  volatility_threshold?: number;
  correlation_threshold?: number;
  use_momentum?: boolean;
  use_value?: boolean;
  risk_tolerance?: string;
  exclude_sectors?: string[];
  include_commodities?: boolean;
  include_bonds?: boolean;
}

export default function StrategyPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<StrategyConfig>({});
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Load current configuration
    loadConfig();
  }, [router]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await strategyService.getConfig();
      setConfig(data);
    } catch (err) {
      setError('Failed to load strategy configuration');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      
      await strategyService.updateConfig(config);
      setSuccess('Strategy configuration saved successfully!');
      
      // Trigger rebalance with new config
      await strategyService.rebalance();
    } catch (err) {
      setError('Failed to save strategy configuration');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof StrategyConfig, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <LoadingSkeleton />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Strategy Configuration</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      <Card className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Portfolio Constraints</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Minimum Market Cap (Millions)
            </label>
            <input
              type="number"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={config.min_market_cap || 0}
              onChange={(e) => handleInputChange('min_market_cap', parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Maximum Assets in Portfolio
            </label>
            <input
              type="number"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={config.max_assets || 10}
              onChange={(e) => handleInputChange('max_assets', parseInt(e.target.value))}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Rebalance Frequency
            </label>
            <select
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={config.rebalance_frequency || 'daily'}
              onChange={(e) => handleInputChange('rebalance_frequency', e.target.value)}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Risk Tolerance
            </label>
            <select
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={config.risk_tolerance || 'moderate'}
              onChange={(e) => handleInputChange('risk_tolerance', e.target.value)}
            >
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>
        </div>
      </Card>

      <Card className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Risk Management</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Volatility Threshold (%)
            </label>
            <input
              type="number"
              step="0.1"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={config.volatility_threshold || 25}
              onChange={(e) => handleInputChange('volatility_threshold', parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Correlation Threshold
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={config.correlation_threshold || 0.7}
              onChange={(e) => handleInputChange('correlation_threshold', parseFloat(e.target.value))}
            />
          </div>
        </div>
      </Card>

      <Card className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Strategy Factors</h2>
        
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              checked={config.use_momentum || false}
              onChange={(e) => handleInputChange('use_momentum', e.target.checked)}
            />
            <span>Use Momentum Factor</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              checked={config.use_value || false}
              onChange={(e) => handleInputChange('use_value', e.target.checked)}
            />
            <span>Use Value Factor</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              checked={config.include_commodities || false}
              onChange={(e) => handleInputChange('include_commodities', e.target.checked)}
            />
            <span>Include Commodities (Gold, Silver, Oil)</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              checked={config.include_bonds || false}
              onChange={(e) => handleInputChange('include_bonds', e.target.checked)}
            />
            <span>Include Bonds (TLT, IEF)</span>
          </label>
        </div>
      </Card>

      <div className="flex gap-4">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="flex-1"
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </Button>

        <Button
          onClick={loadConfig}
          variant="secondary"
          className="flex-1"
        >
          Reset to Current
        </Button>
      </div>

      <Card className="mt-8 bg-blue-50">
        <h3 className="text-lg font-semibold mb-2">How Strategy Configuration Works</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li>• <strong>Portfolio Constraints</strong> control which assets are included and how often rebalancing occurs</li>
          <li>• <strong>Risk Management</strong> settings filter out assets with excessive volatility or correlation</li>
          <li>• <strong>Strategy Factors</strong> enable advanced portfolio optimization techniques</li>
          <li>• Changes take effect immediately after saving and trigger an automatic rebalance</li>
        </ul>
      </Card>
    </div>
  );
}