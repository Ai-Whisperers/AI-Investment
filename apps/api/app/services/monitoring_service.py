"""
Real-time Monitoring and Alerting Service
Tracks system health, signal performance, and sends critical alerts
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import httpx
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.cache import get_cache
from app.models.signals import Signal
from app.models.portfolio import Portfolio
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System health metrics."""
    timestamp: datetime
    database_connected: bool
    cache_connected: bool
    api_latency: float  # milliseconds
    memory_usage: float  # percentage
    cpu_usage: float  # percentage
    active_connections: int
    error_rate: float  # errors per minute
    signal_processing_rate: float  # signals per minute


@dataclass
class SignalMetrics:
    """Signal performance metrics."""
    total_signals: int
    signals_today: int
    high_confidence_signals: int
    executed_signals: int
    win_rate: float
    average_return: float
    best_performer: Optional[Dict]
    worst_performer: Optional[Dict]
    pending_signals: List[Dict]


@dataclass
class Alert:
    """Alert notification."""
    level: str  # 'info', 'warning', 'critical'
    category: str  # 'system', 'signal', 'performance', 'security'
    title: str
    message: str
    timestamp: datetime
    metadata: Optional[Dict] = None


class MonitoringService:
    """Comprehensive monitoring and alerting service."""
    
    def __init__(self):
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK')
        self.alert_thresholds = {
            'error_rate': 5.0,  # errors per minute
            'api_latency': 1000,  # milliseconds
            'memory_usage': 80,  # percentage
            'cpu_usage': 90,  # percentage
            'signal_confidence': 0.9,  # high confidence threshold
            'extreme_return': 0.5,  # 50% expected return
        }
        self.metrics_history = []
        self.alert_history = []
        
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system health metrics."""
        
        import psutil
        
        # Check database connection
        db_connected = await self._check_database()
        
        # Check cache connection
        cache_connected = await self._check_cache()
        
        # Measure API latency
        api_latency = await self._measure_api_latency()
        
        # Get system resources
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get connection count
        connections = len(psutil.net_connections())
        
        # Calculate error rate from logs
        error_rate = await self._calculate_error_rate()
        
        # Calculate signal processing rate
        signal_rate = await self._calculate_signal_rate()
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            database_connected=db_connected,
            cache_connected=cache_connected,
            api_latency=api_latency,
            memory_usage=memory.percent,
            cpu_usage=cpu_percent,
            active_connections=connections,
            error_rate=error_rate,
            signal_processing_rate=signal_rate
        )
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Keep only last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff
        ]
        
        # Check for alerts
        await self._check_system_alerts(metrics)
        
        return metrics
        
    async def collect_signal_metrics(self, db: Session) -> SignalMetrics:
        """Collect signal performance metrics."""
        
        # Total signals
        total_signals = db.query(func.count(Signal.id)).scalar()
        
        # Signals today
        today = datetime.utcnow().date()
        signals_today = db.query(func.count(Signal.id)).filter(
            func.date(Signal.created_at) == today
        ).scalar()
        
        # High confidence signals
        high_confidence = db.query(func.count(Signal.id)).filter(
            Signal.confidence >= self.alert_thresholds['signal_confidence']
        ).scalar()
        
        # Executed signals
        executed = db.query(func.count(Signal.id)).filter(
            Signal.executed == True
        ).scalar()
        
        # Calculate win rate
        winning_signals = db.query(func.count(Signal.id)).filter(
            and_(
                Signal.executed == True,
                Signal.result > 0
            )
        ).scalar()
        
        win_rate = (winning_signals / executed * 100) if executed > 0 else 0
        
        # Average return
        avg_return_query = db.query(func.avg(Signal.result)).filter(
            Signal.executed == True
        ).scalar()
        avg_return = avg_return_query or 0
        
        # Best performer
        best_signal = db.query(Signal).filter(
            Signal.executed == True
        ).order_by(Signal.result.desc()).first()
        
        best_performer = None
        if best_signal:
            best_performer = {
                'ticker': best_signal.ticker,
                'return': best_signal.result,
                'date': best_signal.created_at.isoformat()
            }
            
        # Worst performer
        worst_signal = db.query(Signal).filter(
            Signal.executed == True
        ).order_by(Signal.result.asc()).first()
        
        worst_performer = None
        if worst_signal:
            worst_performer = {
                'ticker': worst_signal.ticker,
                'return': worst_signal.result,
                'date': worst_signal.created_at.isoformat()
            }
            
        # Pending high-confidence signals
        pending = db.query(Signal).filter(
            and_(
                Signal.executed == False,
                Signal.confidence >= 0.8
            )
        ).order_by(Signal.confidence.desc()).limit(10).all()
        
        pending_signals = [
            {
                'ticker': s.ticker,
                'confidence': s.confidence,
                'expected_return': s.expected_return,
                'signal_type': s.signal_type
            }
            for s in pending
        ]
        
        metrics = SignalMetrics(
            total_signals=total_signals,
            signals_today=signals_today,
            high_confidence_signals=high_confidence,
            executed_signals=executed,
            win_rate=win_rate,
            average_return=avg_return,
            best_performer=best_performer,
            worst_performer=worst_performer,
            pending_signals=pending_signals
        )
        
        # Check for signal alerts
        await self._check_signal_alerts(metrics, pending)
        
        return metrics
        
    async def send_discord_alert(self, alert: Alert):
        """Send alert to Discord webhook."""
        
        if not self.discord_webhook:
            logger.warning("Discord webhook not configured")
            return
            
        # Color based on level
        colors = {
            'info': 0x3498db,  # Blue
            'warning': 0xf39c12,  # Orange
            'critical': 0xe74c3c  # Red
        }
        
        # Create embed
        embed = {
            "title": f"{alert.level.upper()}: {alert.title}",
            "description": alert.message,
            "color": colors.get(alert.level, 0x95a5a6),
            "fields": [],
            "timestamp": alert.timestamp.isoformat(),
            "footer": {
                "text": f"Waardhaven AutoIndex | {alert.category}"
            }
        }
        
        # Add metadata fields
        if alert.metadata:
            for key, value in alert.metadata.items():
                embed["fields"].append({
                    "name": key.replace('_', ' ').title(),
                    "value": str(value),
                    "inline": True
                })
                
        # Send to Discord
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.discord_webhook,
                    json={"embeds": [embed]}
                )
                
                if response.status_code == 204:
                    logger.info(f"Discord alert sent: {alert.title}")
                else:
                    logger.error(f"Failed to send Discord alert: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            
    async def create_alert(
        self,
        level: str,
        category: str,
        title: str,
        message: str,
        metadata: Optional[Dict] = None
    ):
        """Create and send an alert."""
        
        alert = Alert(
            level=level,
            category=category,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        # Store alert
        self.alert_history.append(alert)
        
        # Send to Discord
        await self.send_discord_alert(alert)
        
        # Log alert
        if level == 'critical':
            logger.error(f"CRITICAL ALERT: {title} - {message}")
        elif level == 'warning':
            logger.warning(f"WARNING: {title} - {message}")
        else:
            logger.info(f"INFO: {title} - {message}")
            
        return alert
        
    async def _check_database(self) -> bool:
        """Check database connectivity."""
        
        try:
            from app.core.database import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
            
    async def _check_cache(self) -> bool:
        """Check cache connectivity."""
        
        try:
            cache = get_cache()
            await cache.ping()
            return True
        except Exception:
            return False
            
    async def _measure_api_latency(self) -> float:
        """Measure API response time."""
        
        try:
            import time
            start = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/health",
                    timeout=5.0
                )
                
            latency = (time.time() - start) * 1000  # Convert to ms
            return latency
            
        except Exception:
            return 9999  # High value indicates error
            
    async def _calculate_error_rate(self) -> float:
        """Calculate errors per minute from logs."""
        
        # This would normally read from log files or a logging service
        # For now, return a simulated value
        cache = get_cache()
        errors = await cache.get("error_count_last_minute") or 0
        return float(errors)
        
    async def _calculate_signal_rate(self) -> float:
        """Calculate signals processed per minute."""
        
        cache = get_cache()
        signals = await cache.get("signals_processed_last_minute") or 0
        return float(signals)
        
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system-level alerts."""
        
        # Database connectivity
        if not metrics.database_connected:
            await self.create_alert(
                level='critical',
                category='system',
                title='Database Connection Lost',
                message='Unable to connect to database. Immediate action required.',
                metadata={'timestamp': metrics.timestamp.isoformat()}
            )
            
        # High error rate
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            await self.create_alert(
                level='warning',
                category='system',
                title='High Error Rate',
                message=f'Error rate: {metrics.error_rate:.1f} errors/min',
                metadata={'threshold': self.alert_thresholds['error_rate']}
            )
            
        # High memory usage
        if metrics.memory_usage > self.alert_thresholds['memory_usage']:
            await self.create_alert(
                level='warning',
                category='system',
                title='High Memory Usage',
                message=f'Memory usage: {metrics.memory_usage:.1f}%',
                metadata={'threshold': self.alert_thresholds['memory_usage']}
            )
            
        # High API latency
        if metrics.api_latency > self.alert_thresholds['api_latency']:
            await self.create_alert(
                level='warning',
                category='performance',
                title='High API Latency',
                message=f'API latency: {metrics.api_latency:.0f}ms',
                metadata={'threshold': self.alert_thresholds['api_latency']}
            )
            
    async def _check_signal_alerts(self, metrics: SignalMetrics, pending_signals: List[Signal]):
        """Check for signal-related alerts."""
        
        # Extreme return signals
        for signal in pending_signals:
            if signal.expected_return >= self.alert_thresholds['extreme_return']:
                await self.create_alert(
                    level='info',
                    category='signal',
                    title=f'🚀 Extreme Alpha Signal: {signal.ticker}',
                    message=f'Expected return: {signal.expected_return*100:.0f}%',
                    metadata={
                        'confidence': f'{signal.confidence*100:.0f}%',
                        'signal_type': signal.signal_type,
                        'pattern': signal.pattern_stack
                    }
                )
                
        # Daily summary if market close
        now = datetime.utcnow()
        if now.hour == 21 and now.minute < 5:  # 4 PM EST
            await self.create_alert(
                level='info',
                category='performance',
                title='Daily Performance Summary',
                message=f'Signals today: {metrics.signals_today} | Win rate: {metrics.win_rate:.1f}%',
                metadata={
                    'total_signals': metrics.total_signals,
                    'executed': metrics.executed_signals,
                    'avg_return': f'{metrics.average_return:.2f}%',
                    'pending': len(metrics.pending_signals)
                }
            )
            
    async def get_health_status(self) -> Dict:
        """Get overall system health status."""
        
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        if not latest_metrics:
            return {'status': 'unknown', 'message': 'No metrics available'}
            
        # Determine health status
        if not latest_metrics.database_connected:
            status = 'critical'
            message = 'Database offline'
        elif latest_metrics.error_rate > self.alert_thresholds['error_rate']:
            status = 'degraded'
            message = 'High error rate'
        elif latest_metrics.api_latency > self.alert_thresholds['api_latency']:
            status = 'degraded'
            message = 'High latency'
        else:
            status = 'healthy'
            message = 'All systems operational'
            
        return {
            'status': status,
            'message': message,
            'metrics': asdict(latest_metrics),
            'timestamp': latest_metrics.timestamp.isoformat()
        }
        
    async def run_monitoring_loop(self):
        """Run continuous monitoring loop."""
        
        logger.info("Starting monitoring service...")
        
        while True:
            try:
                # Collect metrics every minute
                system_metrics = await self.collect_system_metrics()
                
                # Collect signal metrics every 5 minutes
                if datetime.utcnow().minute % 5 == 0:
                    db = next(get_db())
                    signal_metrics = await self.collect_signal_metrics(db)
                    db.close()
                    
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)


# Global monitoring instance
_monitoring_service = None


def get_monitoring_service() -> MonitoringService:
    """Get or create monitoring service instance."""
    
    global _monitoring_service
    if not _monitoring_service:
        _monitoring_service = MonitoringService()
    return _monitoring_service


async def start_monitoring():
    """Start the monitoring service."""
    
    service = get_monitoring_service()
    await service.run_monitoring_loop()