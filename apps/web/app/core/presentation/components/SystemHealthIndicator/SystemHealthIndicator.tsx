"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useSystemHealth } from '../../hooks/useSystemHealth';
import { SystemHealthIndicatorProps } from './SystemHealthIndicator.types';
import { 
  healthStatusStyles, 
  containerStyles, 
  headerStyles, 
  detailsStyles,
  loadingSkeletonStyles 
} from './SystemHealthIndicator.styles';
import { HealthStatus } from '../../../domain/entities/SystemHealth';

export default function SystemHealthIndicator({ 
  className = '',
  showDetails = true,
  refreshInterval = 60000
}: SystemHealthIndicatorProps) {
  const router = useRouter();
  const [expanded, setExpanded] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  
  const { 
    health, 
    isLoading, 
    message, 
    requiresAction,
    refresh 
  } = useSystemHealth({ refreshInterval, autoRefresh: true });

  const handleRefresh = async () => {
    await refresh();
    setLastUpdate(new Date());
    setExpanded(false);
  };

  const handleNavigateToDiagnostics = () => {
    router.push('/diagnostics');
    setExpanded(false);
  };

  if (isLoading && !health) {
    return <LoadingSkeleton className={className} />;
  }

  const status = health?.overall || HealthStatus.UNKNOWN;
  const styles = healthStatusStyles[status];

  return (
    <motion.div
      className={`${containerStyles.base} ${className}`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <motion.button
        onClick={() => setExpanded(!expanded)}
        className={`${containerStyles.button} ${styles.bg} ${styles.border}`}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <div className={headerStyles.container}>
          <div className={headerStyles.titleGroup}>
            <span className={`${headerStyles.icon} ${styles.text}`}>
              {styles.icon}
            </span>
            <div className={headerStyles.textGroup}>
              <p className={headerStyles.title}>System Status</p>
              <p className={headerStyles.subtitle}>{message}</p>
            </div>
          </div>
          <div className="text-right">
            <p className={headerStyles.timestamp}>
              Updated {lastUpdate.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </p>
            {showDetails && (
              <motion.div
                animate={{ rotate: expanded ? 180 : 0 }}
                transition={{ duration: 0.2 }}
                className={headerStyles.chevron}
              >
                ▼
              </motion.div>
            )}
          </div>
        </div>
      </motion.button>

      {showDetails && (
        <AnimatePresence>
          {expanded && health && (
            <motion.div
              initial={{ opacity: 0, height: 0, y: -10 }}
              animate={{ opacity: 1, height: 'auto', y: 0 }}
              exit={{ opacity: 0, height: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className={detailsStyles.container}
            >
              <div className={detailsStyles.section}>
                <HealthMetric
                  label="Database"
                  sublabel={`${health.database.recordCount.toLocaleString()} records`}
                  status={health.database.simulationReady ? HealthStatus.HEALTHY : HealthStatus.ERROR}
                  statusText={health.database.simulationReady ? ' Ready' : ' Not Ready'}
                />
                
                <HealthMetric
                  label="Cache"
                  sublabel={`${health.cache.totalEntries.toLocaleString()} entries`}
                  status={health.cache.status}
                  statusText={health.cache.hitRate 
                    ? `${(health.cache.hitRate * 100).toFixed(0)}% hit rate` 
                    : 'Disconnected'}
                />
                
                <HealthMetric
                  label="Data Freshness"
                  sublabel={`Last updated ${health.dataFreshness.daysOld} days ago`}
                  status={health.dataFreshness.daysOld <= 1 
                    ? HealthStatus.HEALTHY 
                    : health.dataFreshness.daysOld <= 3 
                    ? HealthStatus.WARNING 
                    : HealthStatus.ERROR}
                  statusText={health.dataFreshness.needsUpdate ? ' Needs Update' : ' Fresh'}
                />
              </div>

              <div className={detailsStyles.actions.container}>
                <div className={detailsStyles.actions.buttonGroup}>
                  <button
                    onClick={handleRefresh}
                    className={`${detailsStyles.actions.button} ${detailsStyles.actions.refreshButton}`}
                  >
                    Refresh
                  </button>
                  <button
                    onClick={handleNavigateToDiagnostics}
                    className={`${detailsStyles.actions.button} ${detailsStyles.actions.detailsButton}`}
                  >
                    Details
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </motion.div>
  );
}

// Sub-components
function LoadingSkeleton({ className }: { className: string }) {
  return (
    <div className={`${containerStyles.loading} ${className}`}>
      <div className={loadingSkeletonStyles.container}>
        <div className={loadingSkeletonStyles.dot} />
        <div className={loadingSkeletonStyles.bar} />
      </div>
    </div>
  );
}

function HealthMetric({ 
  label, 
  sublabel, 
  status, 
  statusText 
}: { 
  label: string; 
  sublabel: string; 
  status: HealthStatus; 
  statusText: string;
}) {
  const styles = healthStatusStyles[status];
  
  return (
    <div className={detailsStyles.metric.row}>
      <div>
        <p className={detailsStyles.metric.label}>{label}</p>
        <p className={detailsStyles.metric.sublabel}>{sublabel}</p>
      </div>
      <div className={detailsStyles.metric.status}>
        <span className={`${detailsStyles.metric.value} ${styles.text}`}>
          {statusText}
        </span>
      </div>
    </div>
  );
}