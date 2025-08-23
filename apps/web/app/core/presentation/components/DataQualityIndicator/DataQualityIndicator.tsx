"use client";

import { motion } from 'framer-motion';
import { useDataQuality } from '../../hooks/useDataQuality';
import { DataQualityIndicatorProps, QualityMetricProps } from './DataQualityIndicator.types';
import { 
  containerStyles,
  headerStyles,
  metricStyles,
  actionStyles,
  warningStyles,
  loadingSkeletonStyles,
  getScoreColor
} from './DataQualityIndicator.styles';
import { 
  FreshnessStatus, 
  CompletenessStatus, 
  AccuracyStatus, 
  CoverageStatus 
} from '../../../domain/entities/DataQuality';

export default function DataQualityIndicator({ 
  className = '',
  onRefreshNeeded,
  expectedAssets = 50,
  refreshInterval = 300000
}: DataQualityIndicatorProps) {
  const {
    quality,
    recommendations,
    requiresRefresh,
    isLoading,
    isRefreshing,
    assess,
    triggerRefresh
  } = useDataQuality({ expectedAssets, refreshInterval, autoRefresh: true });

  const handleRefresh = async () => {
    await triggerRefresh();
    if (onRefreshNeeded) {
      onRefreshNeeded();
    }
  };

  if (isLoading && !quality) {
    return <LoadingSkeleton className={className} />;
  }

  const overallScore = quality?.overallScore || 0;
  const assessment = quality?.assessment || 'poor';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`${containerStyles.base} ${className}`}
    >
      {/* Header */}
      <div className={headerStyles.container}>
        <div className={headerStyles.titleGroup}>
          <h3 className={headerStyles.title}>Data Quality</h3>
          <p className={headerStyles.subtitle}>
            Overall: {assessment.charAt(0).toUpperCase() + assessment.slice(1)}
          </p>
        </div>
        <div className={headerStyles.scoreGroup}>
          <div className={`${headerStyles.scoreValue} ${getScoreColor(overallScore)}`}>
            {overallScore}
          </div>
          <div className={headerStyles.scoreLabel}>Score</div>
        </div>
      </div>

      {/* Quality Metrics */}
      {quality && (
        <div className={metricStyles.container}>
          <QualityMetric
            label="Freshness"
            score={quality.freshness.score}
            status={quality.freshness.status}
            detail={quality.freshness.daysOld === 0 
              ? 'Up to date' 
              : `${quality.freshness.daysOld} days old`}
            icon={getStatusIcon(quality.freshness.status)}
          />
          
          <QualityMetric
            label="Completeness"
            score={quality.completeness.score}
            status={quality.completeness.status}
            detail={`${quality.completeness.totalAssets} assets${
              quality.completeness.missingAssets > 0 
                ? ` (${quality.completeness.missingAssets} missing)` 
                : ''
            }`}
            icon={getStatusIcon(quality.completeness.status)}
          />
          
          <QualityMetric
            label="Accuracy"
            score={quality.accuracy.score}
            status={quality.accuracy.status}
            detail={`${quality.accuracy.validationsPassed}/${quality.accuracy.totalValidations} checks passed`}
            icon={getStatusIcon(quality.accuracy.status)}
          />
          
          <QualityMetric
            label="Coverage"
            score={quality.coverage.score}
            status={quality.coverage.status}
            detail={`${quality.coverage.sectors} sectors, ${quality.coverage.regions} regions`}
            icon={getStatusIcon(quality.coverage.status)}
          />
        </div>
      )}

      {/* Actions */}
      <div className={actionStyles.container}>
        <RefreshButton
          requiresRefresh={requiresRefresh}
          isRefreshing={isRefreshing}
          onClick={handleRefresh}
        />
        <button
          onClick={assess}
          className={actionStyles.assessButton}
        >
          
        </button>
      </div>

      {/* Warning */}
      {overallScore < 60 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={warningStyles.container}
        >
          <p className={warningStyles.text}>
            ️ Data quality is below acceptable thresholds. Consider refreshing market data.
          </p>
        </motion.div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="mt-3 text-xs text-gray-400">
          {recommendations.slice(0, 2).map((rec, idx) => (
            <div key={idx}>• {rec}</div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// Sub-components
function LoadingSkeleton({ className }: { className: string }) {
  return (
    <div className={`${containerStyles.loading} ${className}`}>
      <div className={loadingSkeletonStyles.header}>
        <div className={loadingSkeletonStyles.title} />
        <div className={loadingSkeletonStyles.score} />
      </div>
      <div className={loadingSkeletonStyles.metrics}>
        <div className={loadingSkeletonStyles.metricBar} />
        <div className={loadingSkeletonStyles.metricBar75} />
      </div>
    </div>
  );
}

function QualityMetric({ label, score, status, detail, icon }: QualityMetricProps) {
  const scoreColor = getScoreColor(score);
  
  return (
    <div className={metricStyles.row}>
      <div className={metricStyles.labelGroup}>
        <span className={`${metricStyles.icon} ${scoreColor}`}>
          {icon}
        </span>
        <div>
          <p className={metricStyles.label}>{label}</p>
          <p className={metricStyles.sublabel}>{detail}</p>
        </div>
      </div>
      <span className={`${metricStyles.score} ${scoreColor}`}>
        {score.toFixed(0)}
      </span>
    </div>
  );
}

function RefreshButton({ 
  requiresRefresh, 
  isRefreshing, 
  onClick 
}: {
  requiresRefresh: boolean;
  isRefreshing: boolean;
  onClick: () => void;
}) {
  const buttonStyle = requiresRefresh 
    ? actionStyles.refreshButton.critical
    : actionStyles.refreshButton.normal;

  return (
    <button
      onClick={onClick}
      disabled={isRefreshing}
      className={`${actionStyles.refreshButton.base} ${buttonStyle}`}
    >
      {isRefreshing ? ' Refreshing...' : ' Refresh Data'}
    </button>
  );
}

function getStatusIcon(status: string): string {
  if (status === FreshnessStatus.EXCELLENT || 
      status === CompletenessStatus.COMPLETE || 
      status === AccuracyStatus.ACCURATE || 
      status === CoverageStatus.FULL) {
    return '●';
  }
  if (status === FreshnessStatus.GOOD || 
      status === CompletenessStatus.PARTIAL || 
      status === AccuracyStatus.MINOR_ISSUES || 
      status === CoverageStatus.PARTIAL) {
    return '◐';
  }
  return '○';
}