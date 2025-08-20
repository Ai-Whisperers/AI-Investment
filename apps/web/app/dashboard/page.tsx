"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../core/presentation/contexts/AuthContext";
import { DashboardProvider, useDashboard } from "./providers/DashboardProvider";
import { DashboardLayout } from "./components/DashboardLayout";
import { DashboardMetrics } from "./components/DashboardMetrics";
import { PortfolioChart } from "./components/PortfolioChart";
import { AllocationChart } from "./components/AllocationChart";
import { ChartControls } from "./components/ChartControls";
import { SimulationPanel } from "./components/SimulationPanel";
import AdvancedAnalytics from "../components/dashboard/AdvancedAnalytics";

function DashboardContent() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const {
    // Data
    indexSeries,
    spSeries,
    allocations,
    currencies,
    riskMetrics,
    loading,
    refreshing,
    assetSeriesData,
    loadingAssets,
    loadDashboardData,
    refreshDashboardData,
    
    // Simulation
    amount,
    setAmount,
    currency,
    setCurrency,
    startDate,
    setStartDate,
    simResult,
    simulating,
    runSimulation,
    
    // Chart controls
    chartTimeRange,
    setChartTimeRange,
    showComparison,
    setShowComparison,
    showMovingAverage,
    setShowMovingAverage,
    showVolatilityBands,
    setShowVolatilityBands,
    individualAssets,
    setIndividualAssets,
    hoveredAsset,
    setHoveredAsset,
    showAdvancedAnalytics,
    setShowAdvancedAnalytics,
    filterDataByRange,
    calculateMovingAverage,
    calculateVolatility
  } = useDashboard();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }
    
    if (!authLoading && isAuthenticated) {
      loadDashboardData();
    }
  }, [isAuthenticated, authLoading, router, loadDashboardData]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-white text-center">
          <svg className="animate-spin h-12 w-12 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-lg">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout
      refreshing={refreshing}
      onRefresh={refreshDashboardData}
      showAdvancedAnalytics={showAdvancedAnalytics}
      setShowAdvancedAnalytics={setShowAdvancedAnalytics}
    >
      <div className="space-y-8">
        <DashboardMetrics
          indexSeries={indexSeries}
          spSeries={spSeries}
          riskMetrics={riskMetrics}
          simResult={simResult}
          currency={currency}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <PortfolioChart
              indexSeries={indexSeries}
              spSeries={spSeries}
              assetSeriesData={assetSeriesData}
              individualAssets={individualAssets}
              showComparison={showComparison}
              showMovingAverage={showMovingAverage}
              showVolatilityBands={showVolatilityBands}
              filterDataByRange={filterDataByRange}
              calculateMovingAverage={calculateMovingAverage}
              calculateVolatility={calculateVolatility}
            />
            
            {showAdvancedAnalytics && (
              <div className="mt-6">
                <AdvancedAnalytics allocations={allocations} />
              </div>
            )}
          </div>

          <div className="space-y-6">
            <ChartControls
              chartTimeRange={chartTimeRange}
              setChartTimeRange={setChartTimeRange}
              showComparison={showComparison}
              setShowComparison={setShowComparison}
              showMovingAverage={showMovingAverage}
              setShowMovingAverage={setShowMovingAverage}
              showVolatilityBands={showVolatilityBands}
              setShowVolatilityBands={setShowVolatilityBands}
              individualAssets={individualAssets}
              setIndividualAssets={setIndividualAssets}
              allocations={allocations}
              loadingAssets={loadingAssets}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SimulationPanel
            amount={amount}
            setAmount={setAmount}
            currency={currency}
            setCurrency={setCurrency}
            startDate={startDate}
            setStartDate={setStartDate}
            currencies={currencies}
            simulating={simulating}
            runSimulation={runSimulation}
          />
          
          <AllocationChart
            allocations={allocations}
            hoveredAsset={hoveredAsset}
            setHoveredAsset={setHoveredAsset}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}

export default function Dashboard() {
  return (
    <DashboardProvider>
      <DashboardContent />
    </DashboardProvider>
  );
}