"""
Advanced Asset Classification System with Supply Chain Mapping
Provides comprehensive metadata, industry classification, and dependency tracking
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.asset import Asset

logger = logging.getLogger(__name__)


class Sector(Enum):
    """Primary sector classification with high granularity."""
    # Technology
    TECH_SOFTWARE = "tech_software"
    TECH_HARDWARE = "tech_hardware"
    TECH_SEMICONDUCTORS = "tech_semiconductors"
    TECH_CLOUD = "tech_cloud"
    TECH_AI_ML = "tech_ai_ml"
    TECH_CYBERSECURITY = "tech_cybersecurity"
    TECH_FINTECH = "tech_fintech"
    
    # Finance
    FINANCE_BANKING = "finance_banking"
    FINANCE_INSURANCE = "finance_insurance"
    FINANCE_ASSET_MGMT = "finance_asset_management"
    FINANCE_PAYMENTS = "finance_payments"
    FINANCE_CRYPTO = "finance_crypto"
    FINANCE_REITS = "finance_reits"
    
    # Healthcare
    HEALTH_PHARMA = "health_pharmaceuticals"
    HEALTH_BIOTECH = "health_biotechnology"
    HEALTH_DEVICES = "health_medical_devices"
    HEALTH_SERVICES = "health_services"
    HEALTH_DIGITAL = "health_digital"
    
    # Consumer
    CONSUMER_RETAIL = "consumer_retail"
    CONSUMER_ECOMMERCE = "consumer_ecommerce"
    CONSUMER_GOODS = "consumer_goods"
    CONSUMER_LUXURY = "consumer_luxury"
    CONSUMER_FOOD = "consumer_food_beverage"
    
    # Industrial
    INDUSTRIAL_MANUFACTURING = "industrial_manufacturing"
    INDUSTRIAL_AEROSPACE = "industrial_aerospace"
    INDUSTRIAL_DEFENSE = "industrial_defense"
    INDUSTRIAL_LOGISTICS = "industrial_logistics"
    INDUSTRIAL_CONSTRUCTION = "industrial_construction"
    
    # Energy & Resources
    ENERGY_OIL_GAS = "energy_oil_gas"
    ENERGY_RENEWABLE = "energy_renewable"
    ENERGY_UTILITIES = "energy_utilities"
    RESOURCES_MINING = "resources_mining"
    RESOURCES_AGRICULTURE = "resources_agriculture"
    
    # Emerging
    EMERGING_SPACE = "emerging_space"
    EMERGING_ROBOTICS = "emerging_robotics"
    EMERGING_AGTECH = "emerging_agtech"
    EMERGING_QUANTUM = "emerging_quantum"
    EMERGING_SYNTHETIC_BIO = "emerging_synthetic_biology"
    
    # Commodities
    COMMODITY_METALS = "commodity_metals"
    COMMODITY_ENERGY = "commodity_energy"
    COMMODITY_AGRICULTURE = "commodity_agriculture"
    COMMODITY_CURRENCY = "commodity_currency"


@dataclass
class SupplyChainNode:
    """Represents a node in the supply chain."""
    company: str
    ticker: str
    relationship_type: str  # 'supplier', 'customer', 'partner', 'competitor'
    dependency_level: float  # 0-1 score of how critical this relationship is
    revenue_impact: Optional[float] = None  # Estimated % of revenue
    description: Optional[str] = None


@dataclass
class AssetMetadata:
    """Comprehensive metadata for an asset."""
    # Basic info
    ticker: str
    name: str
    sector: Sector
    subsectors: List[str] = field(default_factory=list)
    
    # Financial metrics
    market_cap: Optional[float] = None
    revenue: Optional[float] = None
    profit_margin: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    
    # Growth metrics
    revenue_growth_yoy: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None
    expected_growth_rate: Optional[float] = None
    
    # Risk factors
    beta: Optional[float] = None
    volatility: Optional[float] = None
    debt_to_equity: Optional[float] = None
    regulatory_risk: Optional[str] = None  # 'low', 'medium', 'high'
    
    # Innovation metrics
    r_and_d_percentage: Optional[float] = None
    patent_count: Optional[int] = None
    ai_adoption_score: Optional[float] = None  # 0-1 score
    
    # ESG scores
    esg_total: Optional[float] = None
    environmental_score: Optional[float] = None
    social_score: Optional[float] = None
    governance_score: Optional[float] = None
    
    # Supply chain
    supply_chain: List[SupplyChainNode] = field(default_factory=list)
    geographic_exposure: Dict[str, float] = field(default_factory=dict)  # Country: revenue %
    
    # Investment characteristics
    liquidity_score: Optional[float] = None  # 0-1 score
    institutional_ownership: Optional[float] = None  # Percentage
    insider_ownership: Optional[float] = None  # Percentage
    short_interest: Optional[float] = None  # Percentage
    
    # Tags for filtering
    tags: Set[str] = field(default_factory=set)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    data_quality_score: float = 0.5  # 0-1 score of data completeness


class AssetClassificationSystem:
    """Advanced asset classification and supply chain mapping system."""
    
    def __init__(self):
        self.asset_cache: Dict[str, AssetMetadata] = {}
        self.sector_indices: Dict[Sector, Set[str]] = {s: set() for s in Sector}
        self.supply_chain_graph: Dict[str, Set[str]] = {}
        self._initialize_default_classifications()
        
    def _initialize_default_classifications(self):
        """Initialize with known major companies."""
        
        # Tech giants
        self._add_asset(AssetMetadata(
            ticker="AAPL",
            name="Apple Inc.",
            sector=Sector.TECH_HARDWARE,
            subsectors=["smartphones", "computers", "wearables", "services"],
            tags={"mega_cap", "dividend", "innovation", "consumer_tech", "supply_chain_critical"},
            supply_chain=[
                SupplyChainNode("FOXCONN", "2354.TW", "supplier", 0.9, 30, "Primary manufacturer"),
                SupplyChainNode("TSMC", "TSM", "supplier", 0.95, 20, "Chip manufacturer"),
                SupplyChainNode("Samsung", "005930.KS", "supplier", 0.7, 10, "Display supplier"),
                SupplyChainNode("Qualcomm", "QCOM", "supplier", 0.6, 5, "5G modems"),
            ]
        ))
        
        # AI/Cloud leaders
        self._add_asset(AssetMetadata(
            ticker="NVDA",
            name="NVIDIA Corporation",
            sector=Sector.TECH_SEMICONDUCTORS,
            subsectors=["ai_chips", "graphics", "data_center", "automotive"],
            tags={"ai_leader", "high_growth", "volatile", "gpu_monopoly"},
            supply_chain=[
                SupplyChainNode("TSMC", "TSM", "supplier", 1.0, 100, "Sole chip manufacturer"),
                SupplyChainNode("Microsoft", "MSFT", "customer", 0.8, 15, "Azure AI"),
                SupplyChainNode("Amazon", "AMZN", "customer", 0.7, 10, "AWS AI"),
                SupplyChainNode("Tesla", "TSLA", "customer", 0.5, 5, "FSD chips"),
            ]
        ))
        
        # Agro-robotics (emerging)
        self._add_asset(AssetMetadata(
            ticker="DE",
            name="Deere & Company",
            sector=Sector.EMERGING_AGTECH,
            subsectors=["agricultural_machinery", "precision_farming", "autonomous_vehicles"],
            tags={"agtech", "robotics", "esg_positive", "inflation_hedge", "ukraine_beneficiary"},
            supply_chain=[
                SupplyChainNode("CAT", "CAT", "competitor", 0.5, None, "Construction equipment"),
                SupplyChainNode("CNH", "CNHI", "competitor", 0.6, None, "Agricultural equipment"),
                SupplyChainNode("AGCO", "AGCO", "competitor", 0.7, None, "Farm equipment"),
            ],
            geographic_exposure={"US": 0.6, "EU": 0.2, "Brazil": 0.1, "Asia": 0.1}
        ))
        
        # Fintech
        self._add_asset(AssetMetadata(
            ticker="SQ",
            name="Block Inc.",
            sector=Sector.TECH_FINTECH,
            subsectors=["payments", "crypto", "banking", "merchant_services"],
            tags={"fintech", "crypto_exposure", "high_growth", "founder_led"},
            supply_chain=[
                SupplyChainNode("V", "V", "partner", 0.8, 30, "Payment network"),
                SupplyChainNode("MA", "MA", "partner", 0.7, 20, "Payment network"),
                SupplyChainNode("COIN", "COIN", "competitor", 0.5, None, "Crypto trading"),
            ]
        ))
        
        # Space sector
        self._add_asset(AssetMetadata(
            ticker="RKLB",
            name="Rocket Lab USA",
            sector=Sector.EMERGING_SPACE,
            subsectors=["launch_services", "satellite_manufacturing", "space_systems"],
            tags={"space", "high_risk", "government_contracts", "emerging_tech"},
            supply_chain=[
                SupplyChainNode("SpaceX", "PRIVATE", "competitor", 0.9, None, "Launch services"),
                SupplyChainNode("LMT", "LMT", "partner", 0.5, 10, "Defense contracts"),
                SupplyChainNode("NOC", "NOC", "partner", 0.4, 5, "Space systems"),
            ]
        ))
        
    def _add_asset(self, metadata: AssetMetadata):
        """Add asset to the classification system."""
        
        self.asset_cache[metadata.ticker] = metadata
        self.sector_indices[metadata.sector].add(metadata.ticker)
        
        # Build supply chain graph
        for node in metadata.supply_chain:
            if metadata.ticker not in self.supply_chain_graph:
                self.supply_chain_graph[metadata.ticker] = set()
            self.supply_chain_graph[metadata.ticker].add(node.ticker)
            
    def classify_asset(self, ticker: str, db: Session) -> AssetMetadata:
        """Classify an asset and generate comprehensive metadata."""
        
        # Check cache first
        if ticker in self.asset_cache:
            return self.asset_cache[ticker]
            
        # Query database
        asset = db.query(Asset).filter(Asset.symbol == ticker).first()
        if not asset:
            logger.warning(f"Asset {ticker} not found in database")
            return None
            
        # Determine sector based on name/type
        sector = self._infer_sector(asset.name, asset.asset_type)
        
        # Create metadata
        metadata = AssetMetadata(
            ticker=ticker,
            name=asset.name,
            sector=sector,
            subsectors=self._infer_subsectors(asset.name, sector),
            tags=self._generate_tags(asset, sector)
        )
        
        # Infer supply chain relationships
        metadata.supply_chain = self._infer_supply_chain(ticker, sector, db)
        
        # Cache and index
        self._add_asset(metadata)
        
        return metadata
        
    def _infer_sector(self, name: str, asset_type: str) -> Sector:
        """Infer sector from company name and type."""
        
        name_lower = name.lower()
        
        # Technology indicators
        tech_keywords = ["tech", "software", "cloud", "data", "cyber", "digital", "ai", "semiconductor"]
        if any(kw in name_lower for kw in tech_keywords):
            if "semiconductor" in name_lower or "chip" in name_lower:
                return Sector.TECH_SEMICONDUCTORS
            elif "cyber" in name_lower:
                return Sector.TECH_CYBERSECURITY
            elif "cloud" in name_lower:
                return Sector.TECH_CLOUD
            else:
                return Sector.TECH_SOFTWARE
                
        # Finance indicators
        finance_keywords = ["bank", "financial", "capital", "insurance", "asset", "fund", "trust"]
        if any(kw in name_lower for kw in finance_keywords):
            if "bank" in name_lower:
                return Sector.FINANCE_BANKING
            elif "insurance" in name_lower:
                return Sector.FINANCE_INSURANCE
            elif "reit" in asset_type.lower():
                return Sector.FINANCE_REITS
            else:
                return Sector.FINANCE_ASSET_MGMT
                
        # Healthcare indicators
        health_keywords = ["health", "pharma", "bio", "medical", "therapeutics", "diagnostics"]
        if any(kw in name_lower for kw in health_keywords):
            if "bio" in name_lower:
                return Sector.HEALTH_BIOTECH
            elif "pharma" in name_lower:
                return Sector.HEALTH_PHARMA
            else:
                return Sector.HEALTH_SERVICES
                
        # Energy indicators
        energy_keywords = ["energy", "oil", "gas", "solar", "wind", "renewable", "utilities", "power"]
        if any(kw in name_lower for kw in energy_keywords):
            if any(kw in name_lower for kw in ["solar", "wind", "renewable", "clean"]):
                return Sector.ENERGY_RENEWABLE
            elif "utilities" in name_lower or "power" in name_lower:
                return Sector.ENERGY_UTILITIES
            else:
                return Sector.ENERGY_OIL_GAS
                
        # Default to consumer goods
        return Sector.CONSUMER_GOODS
        
    def _infer_subsectors(self, name: str, sector: Sector) -> List[str]:
        """Infer subsectors based on name and primary sector."""
        
        subsectors = []
        name_lower = name.lower()
        
        if sector in [Sector.TECH_SOFTWARE, Sector.TECH_CLOUD]:
            if "saas" in name_lower:
                subsectors.append("saas")
            if "security" in name_lower:
                subsectors.append("security")
            if "data" in name_lower:
                subsectors.append("data_analytics")
            if "ai" in name_lower or "ml" in name_lower:
                subsectors.append("artificial_intelligence")
                
        elif sector in [Sector.HEALTH_PHARMA, Sector.HEALTH_BIOTECH]:
            if "oncology" in name_lower or "cancer" in name_lower:
                subsectors.append("oncology")
            if "gene" in name_lower:
                subsectors.append("gene_therapy")
            if "vaccine" in name_lower:
                subsectors.append("vaccines")
                
        return subsectors
        
    def _generate_tags(self, asset: Asset, sector: Sector) -> Set[str]:
        """Generate filtering tags for the asset."""
        
        tags = set()
        
        # Market cap tags (would need actual market cap data)
        tags.add("mid_cap")  # Default, would calculate from actual data
        
        # Sector-based tags
        if sector in [Sector.TECH_AI_ML, Sector.TECH_SEMICONDUCTORS]:
            tags.add("ai_exposure")
            tags.add("high_growth")
            
        if sector in [Sector.EMERGING_SPACE, Sector.EMERGING_ROBOTICS, Sector.EMERGING_AGTECH]:
            tags.add("emerging_tech")
            tags.add("high_risk")
            tags.add("innovation")
            
        if sector in [Sector.ENERGY_RENEWABLE, Sector.EMERGING_AGTECH]:
            tags.add("esg_positive")
            tags.add("climate_play")
            
        if sector in [Sector.FINANCE_BANKING, Sector.ENERGY_UTILITIES]:
            tags.add("dividend")
            tags.add("defensive")
            
        # Asset type tags
        if asset.asset_type == "ETF":
            tags.add("etf")
            tags.add("diversified")
        elif asset.asset_type == "REIT":
            tags.add("reit")
            tags.add("income")
            
        return tags
        
    def _infer_supply_chain(self, ticker: str, sector: Sector, db: Session) -> List[SupplyChainNode]:
        """Infer supply chain relationships based on sector."""
        
        supply_chain = []
        
        # Sector-specific supply chain patterns
        if sector == Sector.TECH_SEMICONDUCTORS:
            # All semiconductor companies depend on TSMC
            supply_chain.append(
                SupplyChainNode("TSMC", "TSM", "supplier", 0.8, 50, "Chip manufacturing")
            )
            # Equipment suppliers
            supply_chain.append(
                SupplyChainNode("ASML", "ASML", "supplier", 0.7, 10, "Lithography equipment")
            )
            
        elif sector in [Sector.TECH_HARDWARE, Sector.CONSUMER_GOODS]:
            # Hardware companies often use Foxconn
            supply_chain.append(
                SupplyChainNode("Foxconn", "2354.TW", "supplier", 0.6, 20, "Manufacturing")
            )
            
        elif sector == Sector.EMERGING_AGTECH:
            # AgTech companies compete with traditional agriculture
            supply_chain.extend([
                SupplyChainNode("Monsanto/Bayer", "BAYRY", "competitor", 0.5, None, "Seeds/chemicals"),
                SupplyChainNode("Corteva", "CTVA", "competitor", 0.5, None, "Agricultural solutions"),
            ])
            
        return supply_chain
        
    def find_supply_chain_impacts(self, ticker: str, event_type: str) -> List[Tuple[str, float]]:
        """Find assets that would be impacted by an event affecting the given ticker."""
        
        impacts = []
        
        if ticker not in self.asset_cache:
            return impacts
            
        metadata = self.asset_cache[ticker]
        
        # Direct supply chain impacts
        for node in metadata.supply_chain:
            impact_score = node.dependency_level
            
            # Adjust impact based on event type
            if event_type == "shortage" and node.relationship_type == "supplier":
                impact_score *= 1.5  # Suppliers benefit from shortages
            elif event_type == "bankruptcy" and node.relationship_type == "customer":
                impact_score *= 2.0  # Customers severely impacted
            elif event_type == "innovation" and node.relationship_type == "competitor":
                impact_score *= -1.0  # Competitors negatively impacted
                
            impacts.append((node.ticker, impact_score))
            
        # Second-order effects through the graph
        if ticker in self.supply_chain_graph:
            for connected_ticker in self.supply_chain_graph[ticker]:
                if connected_ticker in self.asset_cache:
                    # Secondary impact is weaker
                    impacts.append((connected_ticker, 0.3))
                    
        return sorted(impacts, key=lambda x: abs(x[1]), reverse=True)
        
    def get_sector_leaders(self, sector: Sector, limit: int = 5) -> List[AssetMetadata]:
        """Get the leading companies in a sector."""
        
        sector_tickers = self.sector_indices.get(sector, set())
        
        # Sort by market cap or other metrics (would need actual data)
        leaders = []
        for ticker in sector_tickers:
            if ticker in self.asset_cache:
                leaders.append(self.asset_cache[ticker])
                
        return leaders[:limit]
        
    def filter_assets(
        self,
        sectors: Optional[List[Sector]] = None,
        tags: Optional[Set[str]] = None,
        min_market_cap: Optional[float] = None,
        max_pe_ratio: Optional[float] = None,
        min_esg_score: Optional[float] = None
    ) -> List[AssetMetadata]:
        """Filter assets based on multiple criteria."""
        
        results = []
        
        for ticker, metadata in self.asset_cache.items():
            # Sector filter
            if sectors and metadata.sector not in sectors:
                continue
                
            # Tag filter
            if tags and not tags.issubset(metadata.tags):
                continue
                
            # Market cap filter
            if min_market_cap and (not metadata.market_cap or metadata.market_cap < min_market_cap):
                continue
                
            # P/E filter
            if max_pe_ratio and (not metadata.pe_ratio or metadata.pe_ratio > max_pe_ratio):
                continue
                
            # ESG filter
            if min_esg_score and (not metadata.esg_total or metadata.esg_total < min_esg_score):
                continue
                
            results.append(metadata)
            
        return results
        
    def get_thematic_portfolio(self, theme: str) -> List[AssetMetadata]:
        """Get assets for a thematic investment portfolio."""
        
        theme_mappings = {
            "ai_revolution": {
                "sectors": [Sector.TECH_AI_ML, Sector.TECH_SEMICONDUCTORS, Sector.TECH_CLOUD],
                "tags": {"ai_exposure", "high_growth"}
            },
            "climate_change": {
                "sectors": [Sector.ENERGY_RENEWABLE, Sector.EMERGING_AGTECH],
                "tags": {"esg_positive", "climate_play"}
            },
            "space_economy": {
                "sectors": [Sector.EMERGING_SPACE, Sector.INDUSTRIAL_AEROSPACE],
                "tags": {"space", "emerging_tech"}
            },
            "aging_population": {
                "sectors": [Sector.HEALTH_PHARMA, Sector.HEALTH_BIOTECH, Sector.HEALTH_DEVICES],
                "tags": {"healthcare", "demographic_play"}
            },
            "fintech_disruption": {
                "sectors": [Sector.TECH_FINTECH, Sector.FINANCE_PAYMENTS],
                "tags": {"fintech", "disruption", "crypto_exposure"}
            },
            "supply_chain_resilience": {
                "sectors": [Sector.INDUSTRIAL_LOGISTICS, Sector.EMERGING_ROBOTICS],
                "tags": {"automation", "supply_chain"}
            }
        }
        
        if theme not in theme_mappings:
            logger.warning(f"Unknown theme: {theme}")
            return []
            
        mapping = theme_mappings[theme]
        return self.filter_assets(
            sectors=mapping.get("sectors"),
            tags=mapping.get("tags")
        )
        
    def export_classification_data(self) -> Dict:
        """Export all classification data for analysis."""
        
        return {
            "total_assets": len(self.asset_cache),
            "sectors": {
                sector.value: list(tickers)
                for sector, tickers in self.sector_indices.items()
                if tickers
            },
            "supply_chain_connections": len(self.supply_chain_graph),
            "assets": {
                ticker: asdict(metadata)
                for ticker, metadata in self.asset_cache.items()
            }
        }


# Global instance
_classification_system = None


def get_classification_system() -> AssetClassificationSystem:
    """Get or create the classification system instance."""
    
    global _classification_system
    if not _classification_system:
        _classification_system = AssetClassificationSystem()
    return _classification_system