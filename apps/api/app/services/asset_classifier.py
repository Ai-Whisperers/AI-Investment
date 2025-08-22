"""Service for classifying and enriching asset data."""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging

from ..models import Asset

logger = logging.getLogger(__name__)


class AssetClassifier:
    """Service for classifying assets based on various criteria."""
    
    # Sector and industry mappings for common stocks
    SECTOR_MAPPINGS = {
        # Technology
        "AAPL": {"sector": "Technology", "industry": "Consumer Electronics", "tags": ["consumer_tech", "smartphone", "ecosystem"]},
        "MSFT": {"sector": "Technology", "industry": "Software", "tags": ["cloud", "enterprise", "ai", "gaming"]},
        "GOOGL": {"sector": "Technology", "industry": "Internet Services", "tags": ["search", "advertising", "ai", "cloud"]},
        "META": {"sector": "Technology", "industry": "Social Media", "tags": ["social", "metaverse", "advertising", "vr"]},
        "NVDA": {"sector": "Technology", "industry": "Semiconductors", "tags": ["ai", "gpu", "datacenter", "gaming"]},
        "AMD": {"sector": "Technology", "industry": "Semiconductors", "tags": ["cpu", "gpu", "datacenter"]},
        "INTC": {"sector": "Technology", "industry": "Semiconductors", "tags": ["cpu", "semiconductor", "foundry"]},
        "CRM": {"sector": "Technology", "industry": "Software", "tags": ["crm", "saas", "enterprise", "cloud"]},
        "ORCL": {"sector": "Technology", "industry": "Software", "tags": ["database", "enterprise", "cloud"]},
        
        # Finance
        "JPM": {"sector": "Finance", "industry": "Banking", "tags": ["banking", "investment_banking", "systemically_important"]},
        "BAC": {"sector": "Finance", "industry": "Banking", "tags": ["banking", "consumer_banking"]},
        "WFC": {"sector": "Finance", "industry": "Banking", "tags": ["banking", "mortgage"]},
        "GS": {"sector": "Finance", "industry": "Investment Banking", "tags": ["investment_banking", "trading"]},
        "MS": {"sector": "Finance", "industry": "Investment Banking", "tags": ["investment_banking", "wealth_management"]},
        "V": {"sector": "Finance", "industry": "Payment Processing", "tags": ["payments", "fintech", "network"]},
        "MA": {"sector": "Finance", "industry": "Payment Processing", "tags": ["payments", "fintech", "network"]},
        "PYPL": {"sector": "Finance", "industry": "Payment Processing", "tags": ["payments", "fintech", "digital_wallet"]},
        
        # Healthcare
        "JNJ": {"sector": "Healthcare", "industry": "Pharmaceuticals", "tags": ["pharma", "consumer_health", "medical_devices"]},
        "PFE": {"sector": "Healthcare", "industry": "Pharmaceuticals", "tags": ["pharma", "vaccines", "oncology"]},
        "UNH": {"sector": "Healthcare", "industry": "Health Insurance", "tags": ["insurance", "managed_care"]},
        "CVS": {"sector": "Healthcare", "industry": "Healthcare Services", "tags": ["pharmacy", "insurance", "retail_health"]},
        "ABBV": {"sector": "Healthcare", "industry": "Pharmaceuticals", "tags": ["pharma", "biotech", "immunology"]},
        "MRK": {"sector": "Healthcare", "industry": "Pharmaceuticals", "tags": ["pharma", "vaccines", "oncology"]},
        
        # Consumer
        "AMZN": {"sector": "Consumer", "industry": "E-Commerce", "tags": ["ecommerce", "cloud", "logistics", "ai"]},
        "TSLA": {"sector": "Consumer", "industry": "Automotive", "tags": ["ev", "renewable", "autonomous", "battery"]},
        "WMT": {"sector": "Consumer", "industry": "Retail", "tags": ["retail", "grocery", "ecommerce"]},
        "HD": {"sector": "Consumer", "industry": "Home Improvement", "tags": ["retail", "home_improvement"]},
        "MCD": {"sector": "Consumer", "industry": "Restaurants", "tags": ["restaurant", "franchise", "fast_food"]},
        "NKE": {"sector": "Consumer", "industry": "Apparel", "tags": ["apparel", "sports", "brand"]},
        "SBUX": {"sector": "Consumer", "industry": "Restaurants", "tags": ["restaurant", "coffee", "brand"]},
        
        # Energy
        "XOM": {"sector": "Energy", "industry": "Oil & Gas", "tags": ["oil", "gas", "integrated_energy"]},
        "CVX": {"sector": "Energy", "industry": "Oil & Gas", "tags": ["oil", "gas", "integrated_energy"]},
        "COP": {"sector": "Energy", "industry": "Oil & Gas", "tags": ["oil", "gas", "exploration"]},
        "NEE": {"sector": "Energy", "industry": "Utilities", "tags": ["renewable", "utility", "wind", "solar"]},
        
        # Industrial
        "BA": {"sector": "Industrial", "industry": "Aerospace", "tags": ["aerospace", "defense", "aviation"]},
        "CAT": {"sector": "Industrial", "industry": "Machinery", "tags": ["construction", "mining", "machinery"]},
        "GE": {"sector": "Industrial", "industry": "Conglomerate", "tags": ["industrial", "aviation", "energy", "healthcare"]},
        "UPS": {"sector": "Industrial", "industry": "Logistics", "tags": ["logistics", "shipping", "supply_chain"]},
        "HON": {"sector": "Industrial", "industry": "Conglomerate", "tags": ["industrial", "aerospace", "automation"]},
    }
    
    @classmethod
    def classify_by_market_cap(cls, market_cap: Optional[int]) -> str:
        """Classify asset by market cap."""
        if not market_cap:
            return None
        
        if market_cap < 300_000_000:
            return "micro"
        elif market_cap < 2_000_000_000:
            return "small"
        elif market_cap < 10_000_000_000:
            return "mid"
        elif market_cap < 200_000_000_000:
            return "large"
        else:
            return "mega"
    
    @classmethod
    def enrich_asset(cls, asset: Asset, db: Session) -> Asset:
        """Enrich asset with classification data."""
        symbol = asset.symbol.upper()
        
        # Apply known mappings
        if symbol in cls.SECTOR_MAPPINGS:
            mapping = cls.SECTOR_MAPPINGS[symbol]
            asset.sector = mapping.get("sector")
            asset.industry = mapping.get("industry")
            asset.tags = mapping.get("tags", [])
        
        # Classify by market cap if available
        if asset.market_cap:
            asset.market_cap_category = cls.classify_by_market_cap(asset.market_cap)
        
        # Add default ESG scores for demo (in production, fetch from ESG data provider)
        if not asset.esg_score and asset.sector:
            # Assign demo ESG scores based on sector
            sector_esg = {
                "Technology": 75,
                "Finance": 70,
                "Healthcare": 80,
                "Consumer": 65,
                "Energy": 55,
                "Industrial": 60
            }
            asset.esg_score = sector_esg.get(asset.sector, 60)
            asset.environmental_score = asset.esg_score - 5
            asset.social_score = asset.esg_score + 5
            asset.governance_score = asset.esg_score
        
        return asset
    
    @classmethod
    def bulk_classify(cls, db: Session, symbols: Optional[List[str]] = None) -> Dict:
        """Classify multiple assets."""
        query = db.query(Asset)
        
        if symbols:
            query = query.filter(Asset.symbol.in_(symbols))
        
        assets = query.all()
        classified_count = 0
        
        for asset in assets:
            try:
                cls.enrich_asset(asset, db)
                classified_count += 1
            except Exception as e:
                logger.error(f"Error classifying asset {asset.symbol}: {e}")
        
        db.commit()
        
        return {
            "total_assets": len(assets),
            "classified": classified_count,
            "success": classified_count == len(assets)
        }
    
    @classmethod
    def identify_supply_chain_dependencies(cls, symbol: str) -> List[str]:
        """Identify supply chain dependencies for an asset."""
        # This is a simplified example - in production, use supply chain data APIs
        dependencies = {
            "AAPL": ["TSM", "QCOM", "SWKS", "AVGO", "FOXCONN"],  # Chip suppliers
            "TSLA": ["PANASONIC", "LG", "CATL", "NVDA"],  # Battery and chip suppliers
            "AMZN": ["UPS", "FEDEX", "MSFT", "GOOGL"],  # Logistics and cloud
            "MSFT": ["INTC", "AMD", "NVDA"],  # Hardware suppliers
        }
        
        return dependencies.get(symbol, [])
    
    @classmethod
    def calculate_volatility(cls, prices: List[float], period: int = 30) -> float:
        """Calculate historical volatility from price data."""
        if len(prices) < period:
            return None
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(daily_return)
        
        # Calculate standard deviation
        if returns:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
            
            # Annualize volatility (assuming 252 trading days)
            return volatility * (252 ** 0.5)
        
        return None