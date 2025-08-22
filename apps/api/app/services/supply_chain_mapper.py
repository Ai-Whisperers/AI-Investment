"""
Supply Chain Dependency Mapper
Maps supply chain relationships to identify risks and opportunities
Based on insight: "Know the supply chain, predict the impact"
"""

from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)


class SupplyChainMapper:
    """
    Maps supply chain dependencies to find hidden opportunities.
    Disruptions in one area = predictable impacts downstream.
    """
    
    # Critical supply chain relationships
    SUPPLY_CHAINS = {
        # Tech hardware supply chain
        "AAPL": {
            "suppliers": ["TSM", "QCOM", "SWKS", "AVGO", "STX", "WDC"],
            "materials": ["Rare earths", "Lithium", "Cobalt"],
            "regions": ["Taiwan", "China", "Vietnam"],
            "vulnerability": 0.7
        },
        "TSLA": {
            "suppliers": ["PANASONIC", "LG", "CATL", "NVDA", "STM"],
            "materials": ["Lithium", "Nickel", "Cobalt", "Rare earths"],
            "regions": ["China", "Japan", "Nevada"],
            "vulnerability": 0.8
        },
        "NVDA": {
            "suppliers": ["TSM", "SK Hynix", "Samsung", "ASML"],
            "materials": ["Silicon", "Rare gases"],
            "regions": ["Taiwan", "South Korea", "Netherlands"],
            "vulnerability": 0.9
        },
        
        # Agriculture supply chain
        "DE": {
            "suppliers": ["Steel producers", "Chip manufacturers", "Hydraulics"],
            "materials": ["Steel", "Semiconductors", "Rubber"],
            "regions": ["US", "Mexico", "Germany"],
            "vulnerability": 0.4
        },
        "AGCO": {
            "suppliers": ["Engine manufacturers", "Electronics", "Steel"],
            "materials": ["Steel", "Aluminum", "Electronics"],
            "regions": ["US", "Brazil", "Europe"],
            "vulnerability": 0.5
        },
        
        # Automotive supply chain
        "F": {
            "suppliers": ["Chip manufacturers", "Battery suppliers", "Steel"],
            "materials": ["Semiconductors", "Lithium", "Steel", "Aluminum"],
            "regions": ["Mexico", "Canada", "China"],
            "vulnerability": 0.6
        },
        "GM": {
            "suppliers": ["LG Energy", "Chip manufacturers", "Parts suppliers"],
            "materials": ["Batteries", "Semiconductors", "Steel"],
            "regions": ["Mexico", "South Korea", "China"],
            "vulnerability": 0.6
        }
    }
    
    # Ukraine-specific supply chains (high impact potential)
    UKRAINE_DEPENDENCIES = {
        "agricultural_exports": {
            "products": ["Wheat", "Corn", "Sunflower oil", "Barley"],
            "dependent_regions": ["Middle East", "Africa", "Europe"],
            "affected_companies": ["ADM", "BG", "AGRO"],
            "disruption_impact": 0.8
        },
        "raw_materials": {
            "products": ["Neon gas", "Palladium", "Titanium", "Iron ore"],
            "dependent_industries": ["Semiconductors", "Aerospace", "Auto catalysts"],
            "affected_companies": ["INTC", "AMD", "BA", "RTX"],
            "disruption_impact": 0.7
        },
        "fertilizer_chain": {
            "products": ["Ammonia", "Potash", "Nitrogen"],
            "dependent_regions": ["Europe", "Brazil", "India"],
            "affected_companies": ["NTR", "MOS", "CF"],
            "disruption_impact": 0.6
        }
    }
    
    # Supply chain risk events to monitor
    RISK_EVENTS = {
        "geopolitical": {
            "Taiwan_tension": {"probability": 0.3, "impact": 0.9, "affected": ["Semiconductors"]},
            "Ukraine_escalation": {"probability": 0.4, "impact": 0.7, "affected": ["Agriculture", "Materials"]},
            "Trade_war_2.0": {"probability": 0.5, "impact": 0.6, "affected": ["All sectors"]}
        },
        "natural": {
            "Climate_events": {"probability": 0.7, "impact": 0.5, "affected": ["Agriculture", "Energy"]},
            "Pandemic_variant": {"probability": 0.2, "impact": 0.8, "affected": ["All sectors"]}
        },
        "technological": {
            "Cyber_attack": {"probability": 0.6, "impact": 0.6, "affected": ["Technology", "Finance"]},
            "Critical_shortage": {"probability": 0.4, "impact": 0.7, "affected": ["Chips", "Batteries"]}
        }
    }
    
    @classmethod
    def map_dependencies(cls, symbol: str) -> Dict:
        """
        Map all dependencies for a given company.
        Identifies vulnerability points and opportunities.
        """
        if symbol not in cls.SUPPLY_CHAINS:
            return {"error": "No supply chain data available"}
        
        chain = cls.SUPPLY_CHAINS[symbol]
        
        # Calculate aggregate risk score
        risk_score = cls._calculate_risk_score(chain)
        
        # Identify critical dependencies
        critical_deps = cls._identify_critical_dependencies(chain)
        
        # Find hedging opportunities
        hedges = cls._find_hedge_opportunities(symbol, chain)
        
        return {
            "symbol": symbol,
            "suppliers": chain["suppliers"],
            "materials": chain["materials"],
            "regions": chain["regions"],
            "vulnerability_score": chain["vulnerability"],
            "aggregate_risk": risk_score,
            "critical_dependencies": critical_deps,
            "hedge_recommendations": hedges,
            "ukraine_exposure": cls._calculate_ukraine_exposure(chain)
        }
    
    @classmethod
    def find_disruption_beneficiaries(cls, disrupted_entity: str) -> List[Dict]:
        """
        Find companies that benefit from supply chain disruptions.
        One company's problem = another's opportunity.
        """
        beneficiaries = []
        
        # Find companies that compete but don't share supply chain
        for symbol, chain in cls.SUPPLY_CHAINS.items():
            if disrupted_entity in chain.get("suppliers", []):
                # This company is affected negatively
                competitors = cls._find_competitors(symbol)
                for competitor in competitors:
                    if competitor not in cls.SUPPLY_CHAINS:
                        continue
                    
                    comp_chain = cls.SUPPLY_CHAINS[competitor]
                    if disrupted_entity not in comp_chain.get("suppliers", []):
                        beneficiaries.append({
                            "symbol": competitor,
                            "reason": f"Competitor to {symbol} without {disrupted_entity} dependency",
                            "opportunity_score": 0.7
                        })
        
        return beneficiaries
    
    @classmethod
    def analyze_ukraine_impact(cls) -> Dict:
        """
        Analyze Ukraine supply chain impacts.
        Special focus due to stakeholder insight on opportunities.
        """
        analysis = {
            "disrupted_supplies": [],
            "beneficiary_companies": [],
            "investment_thesis": ""
        }
        
        for category, data in cls.UKRAINE_DEPENDENCIES.items():
            impact = {
                "category": category,
                "products": data["products"],
                "disruption_level": data["disruption_impact"],
                "affected_companies": data["affected_companies"]
            }
            analysis["disrupted_supplies"].append(impact)
            
            # Find beneficiaries
            if category == "agricultural_exports":
                analysis["beneficiary_companies"].extend([
                    {"symbol": "DE", "reason": "Increased demand for ag equipment"},
                    {"symbol": "AGCO", "reason": "Precision farming adoption"},
                    {"symbol": "ADM", "reason": "Alternative sourcing premium"}
                ])
        
        analysis["investment_thesis"] = (
            "Ukraine disruption creates two opportunities: "
            "1) Ag-tech adoption acceleration (robotics/automation), "
            "2) Alternative supplier premiums (Brazil, US, Canada)"
        )
        
        return analysis
    
    @classmethod
    def predict_cascade_effects(cls, initial_disruption: str) -> List[Dict]:
        """
        Predict cascade effects from supply chain disruptions.
        Like dominoes falling - map the entire sequence.
        """
        cascade = []
        affected = set()
        
        # First order effects
        for symbol, chain in cls.SUPPLY_CHAINS.items():
            if initial_disruption in chain.get("suppliers", []) + chain.get("materials", []):
                affected.add(symbol)
                cascade.append({
                    "order": 1,
                    "symbol": symbol,
                    "impact": "Direct supplier disruption",
                    "severity": 0.8
                })
        
        # Second order effects
        for affected_company in list(affected):
            for symbol, chain in cls.SUPPLY_CHAINS.items():
                if symbol not in affected and affected_company in chain.get("suppliers", []):
                    cascade.append({
                        "order": 2,
                        "symbol": symbol,
                        "impact": f"Indirect via {affected_company}",
                        "severity": 0.5
                    })
        
        return cascade
    
    @classmethod
    def _calculate_risk_score(cls, chain: Dict) -> float:
        """Calculate aggregate supply chain risk."""
        score = chain["vulnerability"]
        
        # Adjust for geographic concentration
        regions = chain.get("regions", [])
        if len(regions) < 3:
            score += 0.1  # Geographic concentration risk
        
        # Adjust for critical materials
        materials = chain.get("materials", [])
        critical_materials = ["Rare earths", "Semiconductors", "Lithium"]
        for material in critical_materials:
            if material in materials:
                score += 0.05
        
        return min(score, 1.0)
    
    @classmethod
    def _identify_critical_dependencies(cls, chain: Dict) -> List[str]:
        """Identify most critical dependencies."""
        critical = []
        
        # Single source suppliers are critical
        suppliers = chain.get("suppliers", [])
        if len(suppliers) == 1:
            critical.append(f"Single supplier: {suppliers[0]}")
        
        # Rare materials are critical
        for material in chain.get("materials", []):
            if material in ["Rare earths", "Neon gas", "Palladium"]:
                critical.append(f"Rare material: {material}")
        
        # High-risk regions are critical
        for region in chain.get("regions", []):
            if region in ["Taiwan", "Ukraine", "China"]:
                critical.append(f"High-risk region: {region}")
        
        return critical
    
    @classmethod
    def _find_hedge_opportunities(cls, symbol: str, chain: Dict) -> List[Dict]:
        """Find hedging opportunities for supply chain risks."""
        hedges = []
        
        # Suggest alternative suppliers
        if "TSM" in chain.get("suppliers", []):
            hedges.append({
                "type": "Alternative supplier",
                "symbol": "INTC",
                "reason": "Domestic chip production"
            })
        
        # Suggest commodity hedges
        if "Lithium" in chain.get("materials", []):
            hedges.append({
                "type": "Commodity hedge",
                "symbol": "LIT",
                "reason": "Lithium ETF for material exposure"
            })
        
        return hedges
    
    @classmethod
    def _calculate_ukraine_exposure(cls, chain: Dict) -> float:
        """Calculate Ukraine exposure for supply chain."""
        exposure = 0.0
        
        if "Ukraine" in chain.get("regions", []):
            exposure += 0.5
        
        # Check for Ukrainian materials
        ukraine_materials = ["Neon gas", "Palladium", "Wheat", "Corn"]
        for material in chain.get("materials", []):
            if material in ukraine_materials:
                exposure += 0.1
        
        return min(exposure, 1.0)
    
    @classmethod
    def _find_competitors(cls, symbol: str) -> List[str]:
        """Find competitor companies."""
        competitors = {
            "AAPL": ["GOOGL", "SAMSUNG", "XIAOMI"],
            "TSLA": ["F", "GM", "RIVN", "LCID"],
            "NVDA": ["AMD", "INTC"],
            "DE": ["AGCO", "CNH", "KUBTY"],
            "F": ["GM", "TSLA", "TM", "HMC"],
        }
        
        return competitors.get(symbol, [])