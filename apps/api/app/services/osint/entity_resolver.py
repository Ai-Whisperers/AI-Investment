"""
Entity Resolution System
Links companies, people, and organizations across multiple data sources
Critical for cross-referencing signals and detecting hidden connections
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents a resolved entity with all known aliases and metadata."""
    primary_id: str  # Primary identifier (usually ticker symbol)
    entity_type: str  # company, person, organization
    names: Set[str] = field(default_factory=set)
    tickers: Set[str] = field(default_factory=set)
    identifiers: Dict[str, str] = field(default_factory=dict)  # CIK, ISIN, etc.
    relationships: List[Tuple[str, str]] = field(default_factory=list)  # (entity_id, relationship_type)
    metadata: Dict = field(default_factory=dict)
    confidence: float = 1.0
    

class EntityResolver:
    """
    Resolves entities across different data sources.
    Handles aliases, misspellings, and different naming conventions.
    """
    
    def __init__(self):
        """Initialize with known entity mappings."""
        self.entities = {}  # primary_id -> Entity
        self.name_index = {}  # normalized_name -> primary_id
        self.ticker_index = {}  # ticker -> primary_id
        self.identifier_index = {}  # (id_type, id_value) -> primary_id
        
        # Initialize with common entities
        self._initialize_known_entities()
    
    def _initialize_known_entities(self):
        """Initialize with commonly referenced entities."""
        # Major companies with multiple names/references
        known_entities = [
            Entity(
                primary_id="AAPL",
                entity_type="company",
                names={"Apple Inc.", "Apple", "Apple Computer", "AAPL"},
                tickers={"AAPL"},
                identifiers={"cik": "0000320193", "isin": "US0378331005"}
            ),
            Entity(
                primary_id="MSFT",
                entity_type="company",
                names={"Microsoft Corporation", "Microsoft", "MSFT"},
                tickers={"MSFT"},
                identifiers={"cik": "0000789019", "isin": "US5949181045"}
            ),
            Entity(
                primary_id="GOOGL",
                entity_type="company",
                names={"Alphabet Inc.", "Google", "Alphabet", "GOOGL", "GOOG"},
                tickers={"GOOGL", "GOOG"},
                identifiers={"cik": "0001652044", "isin": "US02079K3059"}
            ),
            Entity(
                primary_id="META",
                entity_type="company",
                names={"Meta Platforms", "Facebook", "Meta", "FB", "META"},
                tickers={"META", "FB"},  # FB is old ticker
                identifiers={"cik": "0001326801", "isin": "US30303M1027"}
            ),
            Entity(
                primary_id="BRK",
                entity_type="company",
                names={"Berkshire Hathaway", "Berkshire", "BRK.A", "BRK.B"},
                tickers={"BRK.A", "BRK.B", "BRK-A", "BRK-B"},
                identifiers={"cik": "0001067983"}
            ),
            
            # Key people
            Entity(
                primary_id="warren_buffett",
                entity_type="person",
                names={"Warren Buffett", "Buffett", "Warren E. Buffett", "Oracle of Omaha"},
                relationships=[("BRK", "ceo")],
                metadata={"influence_score": 0.95}
            ),
            Entity(
                primary_id="elon_musk",
                entity_type="person",
                names={"Elon Musk", "Musk", "Elon"},
                relationships=[("TSLA", "ceo"), ("SpaceX", "ceo"), ("TWTR", "owner")],
                metadata={"influence_score": 0.98}
            ),
            Entity(
                primary_id="michael_burry",
                entity_type="person",
                names={"Michael Burry", "Burry", "Dr. Michael Burry", "Scion"},
                relationships=[("Scion Asset Management", "founder")],
                metadata={"influence_score": 0.85}
            ),
            
            # Organizations
            Entity(
                primary_id="fed",
                entity_type="organization",
                names={"Federal Reserve", "Fed", "FOMC", "Federal Reserve System"},
                metadata={"influence_score": 1.0}
            ),
            Entity(
                primary_id="sec",
                entity_type="organization",
                names={"SEC", "Securities and Exchange Commission"},
                metadata={"regulatory_body": True}
            )
        ]
        
        for entity in known_entities:
            self.register_entity(entity)
    
    def register_entity(self, entity: Entity):
        """Register an entity in all indexes."""
        self.entities[entity.primary_id] = entity
        
        # Index names
        for name in entity.names:
            normalized = self._normalize_name(name)
            self.name_index[normalized] = entity.primary_id
        
        # Index tickers
        for ticker in entity.tickers:
            self.ticker_index[ticker.upper()] = entity.primary_id
            # Also index without dots/dashes
            clean_ticker = ticker.replace(".", "").replace("-", "").upper()
            self.ticker_index[clean_ticker] = entity.primary_id
        
        # Index other identifiers
        for id_type, id_value in entity.identifiers.items():
            self.identifier_index[(id_type, id_value)] = entity.primary_id
    
    def resolve(self, text: str, context: Optional[Dict] = None) -> Optional[Entity]:
        """
        Resolve text to an entity.
        Context can provide hints about entity type, source, etc.
        """
        # Try exact ticker match first
        entity_id = self.ticker_index.get(text.upper())
        if entity_id:
            return self.entities[entity_id]
        
        # Try normalized name match
        normalized = self._normalize_name(text)
        entity_id = self.name_index.get(normalized)
        if entity_id:
            return self.entities[entity_id]
        
        # Try fuzzy matching
        entity = self._fuzzy_match(text, context)
        if entity:
            return entity
        
        # Try to extract from context
        if context:
            entity = self._resolve_from_context(text, context)
            if entity:
                return entity
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for matching."""
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common suffixes
        suffixes = [
            " inc.", " inc", " incorporated", " corp.", " corp", " corporation",
            " ltd.", " ltd", " limited", " llc", " plc", " ag", " sa", " gmbh"
        ]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        
        # Remove special characters
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _fuzzy_match(self, text: str, context: Optional[Dict] = None) -> Optional[Entity]:
        """
        Fuzzy match text to an entity.
        Uses string similarity and context clues.
        """
        normalized = self._normalize_name(text)
        best_match = None
        best_score = 0
        
        # Check against all known names
        for known_name, entity_id in self.name_index.items():
            score = SequenceMatcher(None, normalized, known_name).ratio()
            
            # Boost score if context matches
            if context and score > 0.6:
                entity = self.entities[entity_id]
                if context.get("entity_type") == entity.entity_type:
                    score *= 1.2
                if context.get("source") == "financial" and entity.entity_type == "company":
                    score *= 1.1
            
            if score > best_score and score > 0.8:  # 80% similarity threshold
                best_score = score
                best_match = entity_id
        
        if best_match:
            return self.entities[best_match]
        
        return None
    
    def _resolve_from_context(self, text: str, context: Dict) -> Optional[Entity]:
        """
        Try to resolve entity using context clues.
        E.g., if context mentions "CEO of Tesla", we know it's Elon Musk.
        """
        # Check for relationship hints
        if "ceo" in text.lower() or "chief executive" in text.lower():
            # Look for company mentions in context
            for company_ticker in self.ticker_index.keys():
                if company_ticker in context.get("full_text", "").upper():
                    # Find CEO of this company
                    for entity in self.entities.values():
                        if entity.entity_type == "person":
                            for rel_id, rel_type in entity.relationships:
                                if rel_id == company_ticker and rel_type == "ceo":
                                    return entity
        
        return None
    
    def link_entities(self, entity1_id: str, entity2_id: str, relationship: str):
        """
        Create a relationship between two entities.
        E.g., link_entities("elon_musk", "TSLA", "ceo")
        """
        if entity1_id in self.entities:
            self.entities[entity1_id].relationships.append((entity2_id, relationship))
        
        if entity2_id in self.entities:
            # Add reverse relationship
            reverse_rel = self._get_reverse_relationship(relationship)
            if reverse_rel:
                self.entities[entity2_id].relationships.append((entity1_id, reverse_rel))
    
    def _get_reverse_relationship(self, relationship: str) -> Optional[str]:
        """Get the reverse of a relationship."""
        reverse_map = {
            "ceo": "has_ceo",
            "owns": "owned_by",
            "subsidiary": "parent",
            "competes_with": "competes_with",
            "supplies": "supplied_by"
        }
        return reverse_map.get(relationship)
    
    def find_related_entities(
        self, 
        entity_id: str, 
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> List[Entity]:
        """
        Find entities related to the given entity.
        Can traverse relationships up to max_depth.
        """
        if entity_id not in self.entities:
            return []
        
        related = set()
        visited = set()
        
        def traverse(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            if current_id in self.entities:
                entity = self.entities[current_id]
                for rel_id, rel_type in entity.relationships:
                    if relationship_types is None or rel_type in relationship_types:
                        related.add(rel_id)
                        traverse(rel_id, depth + 1)
        
        traverse(entity_id, 0)
        
        # Convert IDs to entities
        return [self.entities[eid] for eid in related if eid in self.entities]
    
    def merge_entities(self, entity1_id: str, entity2_id: str) -> Optional[Entity]:
        """
        Merge two entities that are actually the same.
        Useful when discovering that two entries refer to the same thing.
        """
        if entity1_id not in self.entities or entity2_id not in self.entities:
            return None
        
        entity1 = self.entities[entity1_id]
        entity2 = self.entities[entity2_id]
        
        # Merge into entity1
        entity1.names.update(entity2.names)
        entity1.tickers.update(entity2.tickers)
        entity1.identifiers.update(entity2.identifiers)
        entity1.relationships.extend(entity2.relationships)
        entity1.metadata.update(entity2.metadata)
        
        # Update indexes
        for name in entity2.names:
            normalized = self._normalize_name(name)
            self.name_index[normalized] = entity1_id
        
        for ticker in entity2.tickers:
            self.ticker_index[ticker.upper()] = entity1_id
        
        for id_type, id_value in entity2.identifiers.items():
            self.identifier_index[(id_type, id_value)] = entity1_id
        
        # Remove entity2
        del self.entities[entity2_id]
        
        return entity1
    
    def extract_entities_from_text(self, text: str) -> List[Entity]:
        """
        Extract all entities mentioned in a text.
        Uses pattern matching and known entity lookup.
        """
        entities = []
        
        # Look for ticker symbols (1-5 uppercase letters)
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        potential_tickers = re.findall(ticker_pattern, text)
        
        for ticker in potential_tickers:
            if ticker in self.ticker_index:
                entity_id = self.ticker_index[ticker]
                entities.append(self.entities[entity_id])
        
        # Look for known company names
        for name in self.name_index.keys():
            if name in text.lower():
                entity_id = self.name_index[name]
                if self.entities[entity_id] not in entities:
                    entities.append(self.entities[entity_id])
        
        return entities
    
    def calculate_entity_influence(self, entity_id: str) -> float:
        """
        Calculate influence score for an entity based on relationships and metadata.
        """
        if entity_id not in self.entities:
            return 0.0
        
        entity = self.entities[entity_id]
        
        # Base score from metadata
        base_score = entity.metadata.get("influence_score", 0.5)
        
        # Boost based on number of relationships
        relationship_boost = min(len(entity.relationships) * 0.05, 0.3)
        
        # Boost based on entity type
        type_boost = {
            "person": 0.1 if entity.metadata.get("influence_score", 0) > 0.8 else 0,
            "company": 0.1 if len(entity.tickers) > 0 else 0,
            "organization": 0.2 if entity.metadata.get("regulatory_body") else 0.1
        }.get(entity.entity_type, 0)
        
        return min(base_score + relationship_boost + type_boost, 1.0)
    
    def get_statistics(self) -> Dict:
        """Get statistics about resolved entities."""
        stats = {
            "total_entities": len(self.entities),
            "by_type": {},
            "total_relationships": 0,
            "total_names": len(self.name_index),
            "total_tickers": len(self.ticker_index)
        }
        
        for entity in self.entities.values():
            entity_type = entity.entity_type
            stats["by_type"][entity_type] = stats["by_type"].get(entity_type, 0) + 1
            stats["total_relationships"] += len(entity.relationships)
        
        return stats