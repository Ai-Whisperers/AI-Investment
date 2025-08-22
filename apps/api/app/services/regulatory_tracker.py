"""
Regulatory Signal Tracker
Monitors government policies and regulations for investment catalysts
Based on stakeholder insight: "Regulations create predictable gains"
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RegulatoryTracker:
    """
    Tracks regulatory changes that create investment opportunities.
    EU mandates, US spending bills, China tech regulations = alpha
    """
    
    # Active regulatory catalysts
    REGULATORY_CALENDAR = {
        "2025-02": [
            {
                "region": "EU",
                "regulation": "Digital Markets Act Phase 2",
                "sectors": ["Technology", "Finance"],
                "impact": "Big tech breakup potential",
                "beneficiaries": ["Small tech", "Open source"],
                "losers": ["GOOGL", "META", "AMZN"]
            },
            {
                "region": "US",
                "regulation": "Infrastructure Bill Allocation",
                "sectors": ["Industrial", "Energy"],
                "impact": "$550B spending begins",
                "beneficiaries": ["CAT", "DE", "VMC", "MLM"],
                "losers": []
            }
        ],
        "2025-03": [
            {
                "region": "EU",
                "regulation": "Sustainable Agriculture Standards",
                "sectors": ["Agriculture", "Technology"],
                "impact": "Mandatory precision farming",
                "beneficiaries": ["DE", "AGCO", "Robotics"],
                "losers": ["Traditional equipment"]
            },
            {
                "region": "China",
                "regulation": "AI Governance Framework",
                "sectors": ["Technology"],
                "impact": "AI company compliance costs",
                "beneficiaries": ["Compliant AI firms"],
                "losers": ["BABA", "BIDU", "Non-compliant"]
            }
        ],
        "2025-04": [
            {
                "region": "US",
                "regulation": "Hemp/Cotton Subsidy Program",
                "sectors": ["Agriculture", "Textiles"],
                "impact": "New cultivation incentives",
                "beneficiaries": ["Agricultural equipment", "Processing"],
                "losers": ["Synthetic textiles"]
            }
        ],
        "2025-05": [
            {
                "region": "EU",
                "regulation": "Battery Passport Requirement",
                "sectors": ["Energy", "Automotive"],
                "impact": "Supply chain transparency",
                "beneficiaries": ["Battery recyclers", "EU manufacturers"],
                "losers": ["Non-compliant imports"]
            }
        ]
    }
    
    # Regulatory impact patterns from historical data
    IMPACT_PATTERNS = {
        "mandate": {
            "typical_gain": 0.15,  # 15% for beneficiaries
            "timeline": "3-6 months",
            "certainty": 0.85
        },
        "subsidy": {
            "typical_gain": 0.25,  # 25% for recipients
            "timeline": "6-12 months", 
            "certainty": 0.70
        },
        "restriction": {
            "typical_loss": -0.20,  # -20% for targets
            "timeline": "1-3 months",
            "certainty": 0.90
        },
        "spending": {
            "typical_gain": 0.30,  # 30% for contractors
            "timeline": "12-24 months",
            "certainty": 0.60
        }
    }
    
    # Government spending trackers
    SPENDING_SIGNALS = {
        "US": {
            "defense": {"2025_budget": "$886B", "growth": 0.03},
            "infrastructure": {"2025_budget": "$550B", "growth": 0.15},
            "healthcare": {"2025_budget": "$1.7T", "growth": 0.05},
            "energy": {"2025_budget": "$45B", "growth": 0.20}
        },
        "EU": {
            "green_deal": {"2025_budget": "€250B", "growth": 0.25},
            "digital": {"2025_budget": "€150B", "growth": 0.30},
            "defense": {"2025_budget": "€200B", "growth": 0.40}
        },
        "China": {
            "tech_self_reliance": {"2025_budget": "¥1.5T", "growth": 0.35},
            "rural_development": {"2025_budget": "¥800B", "growth": 0.20}
        }
    }
    
    @classmethod
    def get_upcoming_catalysts(cls, horizon_days: int = 90) -> List[Dict]:
        """
        Get regulatory catalysts within specified horizon.
        These are predictable money-making events.
        """
        catalysts = []
        cutoff_date = datetime.now() + timedelta(days=horizon_days)
        
        for month_str, events in cls.REGULATORY_CALENDAR.items():
            # Parse month string to date
            event_date = datetime.strptime(f"{month_str}-01", "%Y-%m-%d")
            
            if event_date <= cutoff_date:
                for event in events:
                    catalysts.append({
                        "date": month_str,
                        "region": event["region"],
                        "regulation": event["regulation"],
                        "impact": event["impact"],
                        "beneficiaries": event["beneficiaries"],
                        "days_until": (event_date - datetime.now()).days,
                        "confidence": cls._calculate_confidence(event)
                    })
        
        # Sort by days until event
        catalysts.sort(key=lambda x: x["days_until"])
        return catalysts
    
    @classmethod
    def identify_beneficiaries(cls, regulation_type: str, sector: str) -> List[str]:
        """
        Identify stocks that benefit from specific regulations.
        This is our "predictable gains" strategy.
        """
        beneficiary_map = {
            ("mandate", "Technology"): ["Compliance software", "Consultants"],
            ("mandate", "Agriculture"): ["DE", "AGCO", "CNH", "Precision ag"],
            ("subsidy", "Energy"): ["Solar", "Wind", "Battery", "Grid"],
            ("subsidy", "Agriculture"): ["Equipment", "Seeds", "Processing"],
            ("spending", "Infrastructure"): ["CAT", "VMC", "MLM", "Construction"],
            ("spending", "Defense"): ["LMT", "RTX", "NOC", "BA"],
            ("restriction", "Technology"): ["Alternatives", "Open source", "Local players"]
        }
        
        return beneficiary_map.get((regulation_type, sector), [])
    
    @classmethod
    def calculate_impact_score(cls, regulation: Dict) -> float:
        """
        Calculate expected impact score for a regulation.
        Higher score = bigger opportunity.
        """
        score = 0.0
        
        # Budget size impact (normalized)
        if "budget" in regulation:
            # Extract numeric value from budget string
            budget_value = cls._parse_budget(regulation["budget"])
            score += min(budget_value / 1000000000000, 1.0) * 0.3  # Normalize to $1T
        
        # Growth rate impact
        if "growth" in regulation:
            score += regulation["growth"] * 0.3
        
        # Certainty impact
        certainty = regulation.get("certainty", 0.5)
        score += certainty * 0.2
        
        # Timeline impact (sooner is better)
        days_until = regulation.get("days_until", 180)
        timeline_score = max(0, (180 - days_until) / 180)
        score += timeline_score * 0.2
        
        return round(score, 3)
    
    @classmethod
    def get_spending_opportunities(cls, min_growth: float = 0.15) -> List[Dict]:
        """
        Identify government spending opportunities.
        Follow the money from government to contractors.
        """
        opportunities = []
        
        for country, sectors in cls.SPENDING_SIGNALS.items():
            for sector, data in sectors.items():
                if data["growth"] >= min_growth:
                    opportunities.append({
                        "country": country,
                        "sector": sector,
                        "budget": data["2025_budget"],
                        "growth": data["growth"],
                        "impact_score": cls.calculate_impact_score(data),
                        "beneficiaries": cls._get_sector_beneficiaries(sector)
                    })
        
        # Sort by impact score
        opportunities.sort(key=lambda x: x["impact_score"], reverse=True)
        return opportunities
    
    @classmethod
    def track_policy_changes(cls) -> List[Dict]:
        """
        Track real-time policy changes and announcements.
        Early detection = alpha generation.
        """
        # Placeholder for real-time tracking
        recent_changes = [
            {
                "date": "2025-01-20",
                "source": "EU Commission",
                "policy": "USB-C mandate expansion",
                "sectors_affected": ["Consumer Electronics"],
                "immediate_impact": "Accessory manufacturers pivot",
                "signal_strength": 0.8
            },
            {
                "date": "2025-01-18",
                "source": "USDA",
                "policy": "Hemp cultivation deregulation",
                "sectors_affected": ["Agriculture", "Textiles"],
                "immediate_impact": "Equipment demand surge",
                "signal_strength": 0.9
            }
        ]
        
        return recent_changes
    
    @classmethod
    def _calculate_confidence(cls, event: Dict) -> float:
        """Calculate confidence in regulatory event impact."""
        base_confidence = 0.5
        
        # Enacted regulations have higher confidence
        if "enacted" in event.get("impact", "").lower():
            base_confidence += 0.3
        
        # EU regulations typically have high follow-through
        if event.get("region") == "EU":
            base_confidence += 0.1
        
        # Near-term events more certain
        if event.get("days_until", 180) < 30:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    @classmethod
    def _parse_budget(cls, budget_str: str) -> float:
        """Parse budget string to numeric value."""
        # Simple parser for demonstration
        import re
        
        # Extract number
        number = re.findall(r'[\d.]+', budget_str)
        if not number:
            return 0
        
        value = float(number[0])
        
        # Handle currency multipliers
        if 'T' in budget_str or '€T' in budget_str:
            value *= 1000000000000
        elif 'B' in budget_str or '€B' in budget_str:
            value *= 1000000000
        elif 'M' in budget_str or '€M' in budget_str:
            value *= 1000000
        
        return value
    
    @classmethod
    def _get_sector_beneficiaries(cls, sector: str) -> List[str]:
        """Get typical beneficiaries for a sector."""
        beneficiaries = {
            "defense": ["LMT", "RTX", "NOC", "BA", "GD"],
            "infrastructure": ["CAT", "DE", "VMC", "MLM", "URI"],
            "green_deal": ["ENPH", "SEDG", "FSLR", "NEE", "BEP"],
            "digital": ["MSFT", "GOOGL", "AMZN", "Cloud providers"],
            "tech_self_reliance": ["TSM", "ASML", "AMAT", "LRCX"]
        }
        
        return beneficiaries.get(sector, [])