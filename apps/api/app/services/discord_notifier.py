"""
Discord Notification Service for Extreme Alpha Signals
Sends real-time alerts for high-confidence trading opportunities
"""

import os
import httpx
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class SignalAlert:
    """Trading signal alert for Discord."""
    ticker: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    expected_return: float
    signal_type: str
    pattern_stack: List[str]
    timeframe: str
    sources: List[str]
    metadata: Optional[Dict] = None


class DiscordNotifier:
    """Discord webhook notification service."""
    
    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK')
        self.enabled = bool(self.webhook_url)
        
        # Rate limiting
        self.rate_limit = 30  # messages per minute
        self.message_times = []
        
        # Alert thresholds
        self.thresholds = {
            'extreme_confidence': 0.9,  # 90% confidence
            'high_confidence': 0.8,     # 80% confidence
            'extreme_return': 0.5,      # 50% expected return
            'high_return': 0.3,         # 30% expected return
        }
        
    async def send_signal_alert(self, alert: SignalAlert):
        """Send trading signal alert to Discord."""
        
        if not self.enabled:
            logger.warning("Discord webhook not configured")
            return False
            
        # Check rate limit
        if not await self._check_rate_limit():
            logger.warning("Discord rate limit exceeded")
            return False
            
        # Determine alert priority
        priority = self._get_alert_priority(alert)
        
        # Create embed based on priority
        embed = self._create_signal_embed(alert, priority)
        
        # Send to Discord
        return await self._send_webhook({"embeds": [embed]})
        
    def _get_alert_priority(self, alert: SignalAlert) -> str:
        """Determine alert priority level."""
        
        if alert.confidence >= self.thresholds['extreme_confidence'] and \
           alert.expected_return >= self.thresholds['extreme_return']:
            return 'extreme'
        elif alert.confidence >= self.thresholds['high_confidence'] and \
             alert.expected_return >= self.thresholds['high_return']:
            return 'high'
        elif alert.confidence >= self.thresholds['high_confidence'] or \
             alert.expected_return >= self.thresholds['high_return']:
            return 'medium'
        else:
            return 'low'
            
    def _create_signal_embed(self, alert: SignalAlert, priority: str) -> Dict:
        """Create Discord embed for signal alert."""
        
        # Priority-based styling
        styles = {
            'extreme': {
                'color': 0xff0000,  # Red
                'emoji': '🚨',
                'title_prefix': 'EXTREME ALPHA SIGNAL'
            },
            'high': {
                'color': 0xffa500,  # Orange
                'emoji': '🔥',
                'title_prefix': 'HIGH CONFIDENCE SIGNAL'
            },
            'medium': {
                'color': 0xffff00,  # Yellow
                'emoji': '⚡',
                'title_prefix': 'SIGNAL ALERT'
            },
            'low': {
                'color': 0x3498db,  # Blue
                'emoji': '📊',
                'title_prefix': 'SIGNAL UPDATE'
            }
        }
        
        style = styles[priority]
        
        # Build embed
        embed = {
            "title": f"{style['emoji']} {style['title_prefix']}: ${alert.ticker}",
            "description": self._create_signal_description(alert),
            "color": style['color'],
            "fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Waardhaven AutoIndex | Extreme Alpha Detection",
                "icon_url": "https://example.com/logo.png"  # Update with actual logo
            }
        }
        
        # Add fields
        embed["fields"].extend([
            {
                "name": "📈 Action",
                "value": f"**{alert.action}**",
                "inline": True
            },
            {
                "name": "💎 Confidence",
                "value": f"{alert.confidence*100:.0f}%",
                "inline": True
            },
            {
                "name": "🚀 Expected Return",
                "value": f"{alert.expected_return*100:.0f}%",
                "inline": True
            },
            {
                "name": "⏰ Timeframe",
                "value": alert.timeframe,
                "inline": True
            },
            {
                "name": "🔍 Signal Type",
                "value": alert.signal_type,
                "inline": True
            },
            {
                "name": "📊 Pattern Stack",
                "value": ", ".join(alert.pattern_stack[:3]),
                "inline": True
            }
        ])
        
        # Add sources
        if alert.sources:
            embed["fields"].append({
                "name": "📡 Sources",
                "value": ", ".join(alert.sources),
                "inline": False
            })
            
        # Add metadata if extreme priority
        if priority == 'extreme' and alert.metadata:
            metadata_str = "\n".join([
                f"**{k}**: {v}" for k, v in alert.metadata.items()
            ])
            embed["fields"].append({
                "name": "📋 Additional Data",
                "value": metadata_str[:1024],  # Discord field limit
                "inline": False
            })
            
        return embed
        
    def _create_signal_description(self, alert: SignalAlert) -> str:
        """Create detailed signal description."""
        
        descriptions = {
            'forty_eight_hour': f"Early signal detected 48 hours before mainstream. {alert.action} ${alert.ticker} with {alert.expected_return*100:.0f}% expected return.",
            'meme_velocity': f"Viral momentum detected! ${alert.ticker} showing explosive social media growth. {alert.expected_return*100:.0f}% potential.",
            'smart_divergence': f"Smart money divergence on ${alert.ticker}. Institutions {alert.action.lower()}ing while retail does opposite.",
            'extreme_event': f"Extreme event pattern detected for ${alert.ticker}. Historical similar patterns returned {alert.expected_return*100:.0f}%.",
            'insider_pattern': f"Unusual insider activity pattern on ${alert.ticker}. Strong {alert.action} signal.",
        }
        
        return descriptions.get(
            alert.signal_type,
            f"High-confidence {alert.action} signal for ${alert.ticker} with {alert.expected_return*100:.0f}% expected return."
        )
        
    async def send_market_summary(self, summary: Dict):
        """Send daily market summary to Discord."""
        
        if not self.enabled:
            return False
            
        embed = {
            "title": "📊 Daily Market Summary",
            "description": f"Performance update for {datetime.utcnow().strftime('%Y-%m-%d')}",
            "color": 0x2ecc71,  # Green
            "fields": [
                {
                    "name": "📈 Signals Generated",
                    "value": str(summary.get('signals_generated', 0)),
                    "inline": True
                },
                {
                    "name": "🎯 Win Rate",
                    "value": f"{summary.get('win_rate', 0):.1f}%",
                    "inline": True
                },
                {
                    "name": "💰 Avg Return",
                    "value": f"{summary.get('avg_return', 0):.2f}%",
                    "inline": True
                },
                {
                    "name": "🔥 Top Performer",
                    "value": f"${summary.get('top_performer', 'N/A')}",
                    "inline": True
                },
                {
                    "name": "📉 Worst Performer",
                    "value": f"${summary.get('worst_performer', 'N/A')}",
                    "inline": True
                },
                {
                    "name": "⏳ Pending Signals",
                    "value": str(summary.get('pending_signals', 0)),
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add top signals
        if 'top_signals' in summary:
            signals_text = "\n".join([
                f"• **${s['ticker']}**: {s['action']} ({s['confidence']*100:.0f}% conf)"
                for s in summary['top_signals'][:5]
            ])
            embed["fields"].append({
                "name": "🎯 Top Signals Today",
                "value": signals_text or "No high-confidence signals",
                "inline": False
            })
            
        return await self._send_webhook({"embeds": [embed]})
        
    async def send_system_alert(self, level: str, title: str, message: str, details: Optional[Dict] = None):
        """Send system health alert to Discord."""
        
        if not self.enabled:
            return False
            
        # Color based on severity
        colors = {
            'critical': 0xe74c3c,  # Red
            'warning': 0xf39c12,   # Orange
            'info': 0x3498db,      # Blue
            'success': 0x2ecc71    # Green
        }
        
        # Emoji based on severity
        emojis = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅'
        }
        
        embed = {
            "title": f"{emojis.get(level, '📢')} {title}",
            "description": message,
            "color": colors.get(level, 0x95a5a6),
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": f"System Alert | {level.upper()}"
            }
        }
        
        # Add details if provided
        if details:
            embed["fields"] = [
                {
                    "name": key.replace('_', ' ').title(),
                    "value": str(value),
                    "inline": True
                }
                for key, value in details.items()
            ]
            
        return await self._send_webhook({"embeds": [embed]})
        
    async def send_performance_update(self, performance: Dict):
        """Send portfolio performance update."""
        
        if not self.enabled:
            return False
            
        # Determine color based on performance
        returns = performance.get('daily_return', 0)
        if returns > 0:
            color = 0x2ecc71  # Green
            emoji = '📈'
        elif returns < 0:
            color = 0xe74c3c  # Red
            emoji = '📉'
        else:
            color = 0x95a5a6  # Gray
            emoji = '➖'
            
        embed = {
            "title": f"{emoji} Portfolio Performance Update",
            "color": color,
            "fields": [
                {
                    "name": "Daily Return",
                    "value": f"{returns:.2f}%",
                    "inline": True
                },
                {
                    "name": "Weekly Return",
                    "value": f"{performance.get('weekly_return', 0):.2f}%",
                    "inline": True
                },
                {
                    "name": "Monthly Return",
                    "value": f"{performance.get('monthly_return', 0):.2f}%",
                    "inline": True
                },
                {
                    "name": "YTD Return",
                    "value": f"{performance.get('ytd_return', 0):.2f}%",
                    "inline": True
                },
                {
                    "name": "Portfolio Value",
                    "value": f"${performance.get('total_value', 0):,.2f}",
                    "inline": True
                },
                {
                    "name": "Active Positions",
                    "value": str(performance.get('active_positions', 0)),
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self._send_webhook({"embeds": [embed]})
        
    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        
        now = datetime.utcnow()
        
        # Remove old timestamps
        self.message_times = [
            t for t in self.message_times
            if (now - t).total_seconds() < 60
        ]
        
        # Check if under limit
        if len(self.message_times) >= self.rate_limit:
            return False
            
        # Add current timestamp
        self.message_times.append(now)
        return True
        
    async def _send_webhook(self, payload: Dict) -> bool:
        """Send payload to Discord webhook."""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 204:
                    logger.info("Discord notification sent successfully")
                    return True
                else:
                    logger.error(f"Discord webhook failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False


# Global notifier instance
_discord_notifier = None


def get_discord_notifier() -> DiscordNotifier:
    """Get or create Discord notifier instance."""
    
    global _discord_notifier
    if not _discord_notifier:
        _discord_notifier = DiscordNotifier()
    return _discord_notifier


async def notify_extreme_signal(
    ticker: str,
    action: str,
    confidence: float,
    expected_return: float,
    signal_type: str,
    pattern_stack: List[str],
    timeframe: str = "2-4 weeks",
    sources: Optional[List[str]] = None,
    metadata: Optional[Dict] = None
):
    """Convenience function to send extreme signal notification."""
    
    notifier = get_discord_notifier()
    
    alert = SignalAlert(
        ticker=ticker,
        action=action,
        confidence=confidence,
        expected_return=expected_return,
        signal_type=signal_type,
        pattern_stack=pattern_stack,
        timeframe=timeframe,
        sources=sources or [],
        metadata=metadata
    )
    
    return await notifier.send_signal_alert(alert)