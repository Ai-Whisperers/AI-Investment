import React, { createContext, useContext, useEffect } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import { useSimulation } from '../../hooks/useSimulation';
import { useChartControls } from '../hooks/useChartControls';

interface DashboardContextType {
  // Data
  indexSeries: any[];
  spSeries: any[];
  allocations: any[];
  currencies: {[key: string]: string};
  riskMetrics: any;
  loading: boolean;
  refreshing: boolean;
  assetSeriesData: {[key: string]: any[]};
  loadingAssets: {[key: string]: boolean};
  
  // Data actions
  loadDashboardData: () => Promise<void>;
  refreshDashboardData: () => Promise<void>;
  fetchAssetData: (symbol: string) => Promise<void>;
  
  // Simulation
  amount: number;
  setAmount: (amount: number) => void;
  currency: string;
  setCurrency: (currency: string) => void;
  startDate: string;
  setStartDate: (date: string) => void;
  simResult: any;
  simulating: boolean;
  runSimulation: () => Promise<void>;
  
  // Chart controls
  chartTimeRange: string;
  setChartTimeRange: (range: string) => void;
  showComparison: boolean;
  setShowComparison: (show: boolean) => void;
  showDataPanel: boolean;
  setShowDataPanel: (show: boolean) => void;
  selectedDataSeries: string[];
  setSelectedDataSeries: (series: string[]) => void;
  showVolume: boolean;
  setShowVolume: (show: boolean) => void;
  showMovingAverage: boolean;
  setShowMovingAverage: (show: boolean) => void;
  showVolatilityBands: boolean;
  setShowVolatilityBands: (show: boolean) => void;
  individualAssets: {[key: string]: boolean};
  setIndividualAssets: React.Dispatch<React.SetStateAction<{[key: string]: boolean}>>;
  hoveredAsset: string | null;
  setHoveredAsset: (asset: string | null) => void;
  showAdvancedAnalytics: boolean;
  setShowAdvancedAnalytics: (show: boolean) => void;
  
  // Chart utilities
  filterDataByRange: (data: any[]) => any[];
  calculateMovingAverage: (data: any[], period?: number) => (number | null)[];
  calculateVolatility: (data: any[], period?: number) => any[];
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return context;
};

interface DashboardProviderProps {
  children: React.ReactNode;
}

export const DashboardProvider: React.FC<DashboardProviderProps> = ({ children }) => {
  const dashboardData = useDashboardData();
  const simulation = useSimulation();
  const chartControls = useChartControls();

  // Fetch asset data when individual assets are selected
  useEffect(() => {
    Object.entries(chartControls.individualAssets).forEach(([symbol, isSelected]) => {
      if (isSelected && !dashboardData.assetSeriesData[symbol] && !dashboardData.loadingAssets[symbol]) {
        dashboardData.fetchAssetData(symbol);
      }
    });
  }, [chartControls.individualAssets, dashboardData]);

  const value: DashboardContextType = {
    ...dashboardData,
    ...simulation,
    ...chartControls
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};