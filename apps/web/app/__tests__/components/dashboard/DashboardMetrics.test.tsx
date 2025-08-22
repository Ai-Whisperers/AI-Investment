/**
 * Tests for DashboardMetrics component
 * Single responsibility: Test metrics display logic
 */

import React from 'react'
import { render, screen } from '../../utils/test-utils'
import { DashboardMetrics } from '@/app/dashboard/components/DashboardMetrics'
import { mockPortfolio } from '../../utils/mock-data'

describe('DashboardMetrics', () => {
  // Test data setup matching actual component props
  const mockSeriesData = [
    { date: '2024-01-01', value: 100000 },
    { date: '2024-01-02', value: 101000 },
    { date: '2024-01-03', value: 102000 },
  ]

  const defaultProps = {
    indexSeries: mockSeriesData,
    spSeries: mockSeriesData,
    riskMetrics: {
      sharpe_ratio: 1.5,
      sortino_ratio: 1.8,
      max_drawdown: -0.15,
      volatility: 0.18,
      beta: 1.0,
      alpha: 0.02,
      correlation_with_market: 0.85,
    },
    simResult: {
      amount_final: 120000,
      roi_pct: 20.0,
      currency: 'USD',
    },
    currency: 'USD',
  }

  describe('Rendering', () => {
    it('should render metric cards', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      // Check for risk metrics
      expect(screen.getByText(/Sharpe Ratio/i)).toBeInTheDocument()
      expect(screen.getByText(/Max Drawdown/i)).toBeInTheDocument()
      expect(screen.getByText(/Volatility/i)).toBeInTheDocument()
    })

    it('should display simulation results when provided', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      // Check if simulation results are displayed
      expect(screen.getByText(/Simulation Results/i)).toBeInTheDocument()
      expect(screen.getByText(/Final Amount/i)).toBeInTheDocument()
      expect(screen.getByText(/\+20\.00%/)).toBeInTheDocument()
    })

    it('should calculate returns correctly', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      // Check if returns section is rendered
      expect(screen.getByText(/Returns/i)).toBeInTheDocument()
      // The component calculates daily, monthly, yearly returns
      expect(screen.getByText(/Daily/i)).toBeInTheDocument()
      expect(screen.getByText(/Monthly/i)).toBeInTheDocument()
    })
  })

  describe('Conditional Rendering', () => {
    it('should show risk metrics when provided', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      expect(screen.getByText('1.50')).toBeInTheDocument() // Sharpe ratio
      expect(screen.getByText('18.00%')).toBeInTheDocument() // Volatility
    })

    it('should handle null risk metrics gracefully', () => {
      const propsWithoutRisk = {
        ...defaultProps,
        riskMetrics: null,
      }
      
      render(<DashboardMetrics {...propsWithoutRisk} />)
      
      // Should show N/A or placeholder
      const naElements = screen.getAllByText('N/A')
      expect(naElements.length).toBeGreaterThan(0)
    })
  })

  describe('Empty State', () => {
    it('should handle empty series data', () => {
      const emptyProps = {
        ...defaultProps,
        indexSeries: [],
        spSeries: [],
      }
      
      render(<DashboardMetrics {...emptyProps} />)
      
      // Should still render without crashing
      expect(screen.getByText(/Returns/i)).toBeInTheDocument()
    })
  })
})