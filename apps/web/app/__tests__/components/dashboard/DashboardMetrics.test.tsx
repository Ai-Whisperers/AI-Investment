/**
 * Tests for DashboardMetrics component
 * Single responsibility: Test metrics display logic
 */

import React from 'react'
import { render, screen } from '../../utils/test-utils'
import { DashboardMetrics } from '@/dashboard/components/DashboardMetrics'
import { mockPortfolio } from '../../utils/mock-data'

describe('DashboardMetrics', () => {
  // Test data setup
  const defaultProps = {
    totalValue: mockPortfolio.total_value,
    totalReturn: mockPortfolio.returns,
    dailyChange: 0.02,
    sharpeRatio: 1.5,
  }

  describe('Rendering', () => {
    it('should render all metric cards', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      expect(screen.getByText(/Total Value/i)).toBeInTheDocument()
      expect(screen.getByText(/Total Return/i)).toBeInTheDocument()
      expect(screen.getByText(/Daily Change/i)).toBeInTheDocument()
      expect(screen.getByText(/Sharpe Ratio/i)).toBeInTheDocument()
    })

    it('should format currency values correctly', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      // Check if total value is formatted as currency
      expect(screen.getByText(/\$100,000/)).toBeInTheDocument()
    })

    it('should display percentage values correctly', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      // Check if percentages are formatted correctly
      expect(screen.getByText(/15\.00%/)).toBeInTheDocument() // Total return
      expect(screen.getByText(/2\.00%/)).toBeInTheDocument() // Daily change
    })
  })

  describe('Conditional Styling', () => {
    it('should apply positive styling for positive returns', () => {
      render(<DashboardMetrics {...defaultProps} />)
      
      const returnElement = screen.getByText(/15\.00%/)
      expect(returnElement).toHaveClass('text-green-600')
    })

    it('should apply negative styling for negative returns', () => {
      const negativeProps = {
        ...defaultProps,
        totalReturn: -0.05,
        dailyChange: -0.01,
      }
      
      render(<DashboardMetrics {...negativeProps} />)
      
      const returnElement = screen.getByText(/-5\.00%/)
      expect(returnElement).toHaveClass('text-red-600')
    })
  })

  describe('Loading State', () => {
    it('should show loading skeleton when data is not available', () => {
      const loadingProps = {
        totalValue: undefined,
        totalReturn: undefined,
        dailyChange: undefined,
        sharpeRatio: undefined,
      }
      
      render(<DashboardMetrics {...loadingProps} />)
      
      // Check for loading skeletons
      const skeletons = screen.getAllByTestId('loading-skeleton')
      expect(skeletons).toHaveLength(4)
    })
  })
})