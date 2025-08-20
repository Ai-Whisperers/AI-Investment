"""
Entity extraction module for news articles.
"""

import logging
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from text."""
    symbol: str
    name: str
    type: str
    mentions: int
    context: List[str]
    sentiment_score: Optional[float] = None


class EntityExtractor:
    """Extracts and identifies entities from news text."""

    # Common stock symbols pattern
    TICKER_PATTERN = re.compile(r'\b[A-Z]{1,5}\b')
    
    # Common company suffixes
    COMPANY_SUFFIXES = {
        'Inc', 'Inc.', 'Corp', 'Corp.', 'Corporation', 'Ltd', 'Ltd.',
        'LLC', 'LLP', 'LP', 'Company', 'Co', 'Co.', 'Group', 'Holdings'
    }
    
    # Entity type classifications
    ENTITY_TYPES = {
        'stock': 'STOCK',
        'company': 'COMPANY',
        'person': 'PERSON',
        'sector': 'SECTOR',
        'commodity': 'COMMODITY',
        'currency': 'CURRENCY',
        'index': 'INDEX'
    }

    def __init__(self, known_symbols: Optional[Dict[str, str]] = None):
        """
        Initialize entity extractor.
        
        Args:
            known_symbols: Dict mapping symbols to company names
        """
        self.known_symbols = known_symbols or {}

    def extract_entities(
        self,
        text: str,
        title: Optional[str] = None
    ) -> List[ExtractedEntity]:
        """
        Extract entities from text.
        
        Args:
            text: Main text to analyze
            title: Optional title for additional context
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract ticker symbols
        tickers = self._extract_tickers(text, title)
        for ticker in tickers:
            entities.append(ticker)
        
        # Extract company names
        companies = self._extract_companies(text, title)
        for company in companies:
            entities.append(company)
        
        # Extract other entity types
        sectors = self._extract_sectors(text)
        for sector in sectors:
            entities.append(sector)
        
        # Deduplicate entities
        entities = self._deduplicate_entities(entities)
        
        return entities

    def _extract_tickers(
        self,
        text: str,
        title: Optional[str] = None
    ) -> List[ExtractedEntity]:
        """Extract stock ticker symbols from text."""
        entities = []
        full_text = f"{title or ''} {text}"
        
        # Find all potential tickers
        potential_tickers = self.TICKER_PATTERN.findall(full_text)
        
        for ticker in potential_tickers:
            # Skip common words that match pattern but aren't tickers
            if ticker in {'A', 'I', 'AT', 'BY', 'IN', 'OF', 'ON', 'OR', 'TO', 'UP'}:
                continue
            
            # Check if it's a known symbol
            if ticker in self.known_symbols:
                entity = ExtractedEntity(
                    symbol=ticker,
                    name=self.known_symbols[ticker],
                    type=self.ENTITY_TYPES['stock'],
                    mentions=full_text.count(ticker),
                    context=self._get_context(full_text, ticker)
                )
                entities.append(entity)
            elif len(ticker) >= 2 and ticker.isupper():
                # Potential unknown ticker
                entity = ExtractedEntity(
                    symbol=ticker,
                    name=ticker,
                    type=self.ENTITY_TYPES['stock'],
                    mentions=full_text.count(ticker),
                    context=self._get_context(full_text, ticker)
                )
                entities.append(entity)
        
        return entities

    def _extract_companies(
        self,
        text: str,
        title: Optional[str] = None
    ) -> List[ExtractedEntity]:
        """Extract company names from text."""
        entities = []
        full_text = f"{title or ''} {text}"
        
        # Look for capitalized phrases that might be company names
        # Pattern: Capitalized words potentially followed by company suffix
        pattern = re.compile(
            r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            r'(?:\s+(?:' + '|'.join(re.escape(s) for s in self.COMPANY_SUFFIXES) + r'))?'
        )
        
        matches = pattern.findall(full_text)
        
        for match in matches:
            match = match.strip()
            if len(match) > 3:  # Skip very short matches
                # Try to find corresponding ticker
                symbol = self._find_symbol_for_company(match)
                
                entity = ExtractedEntity(
                    symbol=symbol or match.replace(' ', '_').upper(),
                    name=match,
                    type=self.ENTITY_TYPES['company'],
                    mentions=full_text.count(match),
                    context=self._get_context(full_text, match)
                )
                entities.append(entity)
        
        return entities

    def _extract_sectors(self, text: str) -> List[ExtractedEntity]:
        """Extract sector mentions from text."""
        entities = []
        
        # Common sector keywords
        sectors = {
            'technology': 'TECH',
            'healthcare': 'HEALTH',
            'finance': 'FIN',
            'financial': 'FIN',
            'energy': 'ENERGY',
            'consumer': 'CONSUMER',
            'industrial': 'INDUSTRIAL',
            'materials': 'MATERIALS',
            'utilities': 'UTILITIES',
            'real estate': 'REALESTATE',
            'communication': 'COMM',
            'retail': 'RETAIL',
            'automotive': 'AUTO',
            'pharmaceutical': 'PHARMA',
            'biotechnology': 'BIOTECH'
        }
        
        text_lower = text.lower()
        
        for sector_name, sector_code in sectors.items():
            if sector_name in text_lower:
                entity = ExtractedEntity(
                    symbol=sector_code,
                    name=sector_name.title(),
                    type=self.ENTITY_TYPES['sector'],
                    mentions=text_lower.count(sector_name),
                    context=self._get_context(text, sector_name)
                )
                entities.append(entity)
        
        return entities

    def _get_context(
        self,
        text: str,
        entity: str,
        context_words: int = 10
    ) -> List[str]:
        """Get context snippets around entity mentions."""
        contexts = []
        text_lower = text.lower()
        entity_lower = entity.lower()
        
        # Find all occurrences
        start = 0
        while True:
            pos = text_lower.find(entity_lower, start)
            if pos == -1:
                break
            
            # Get surrounding words
            words = text.split()
            word_positions = []
            current_pos = 0
            
            for i, word in enumerate(words):
                word_positions.append((current_pos, current_pos + len(word)))
                current_pos += len(word) + 1
            
            # Find which word contains our entity
            entity_word_idx = None
            for i, (start_pos, end_pos) in enumerate(word_positions):
                if start_pos <= pos < end_pos:
                    entity_word_idx = i
                    break
            
            if entity_word_idx is not None:
                # Get context words
                context_start = max(0, entity_word_idx - context_words)
                context_end = min(len(words), entity_word_idx + context_words + 1)
                context = ' '.join(words[context_start:context_end])
                contexts.append(context)
            
            start = pos + 1
            
            # Limit contexts to avoid too much data
            if len(contexts) >= 3:
                break
        
        return contexts

    def _find_symbol_for_company(self, company_name: str) -> Optional[str]:
        """Try to find ticker symbol for company name."""
        # Check if we have a reverse mapping
        for symbol, name in self.known_symbols.items():
            if company_name.lower() in name.lower() or name.lower() in company_name.lower():
                return symbol
        return None

    def _deduplicate_entities(
        self,
        entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """Remove duplicate entities, keeping the most informative one."""
        seen = {}
        
        for entity in entities:
            key = (entity.symbol.upper(), entity.type)
            
            if key not in seen:
                seen[key] = entity
            else:
                # Keep the one with more information
                existing = seen[key]
                if len(entity.name) > len(existing.name):
                    seen[key] = entity
                elif entity.mentions > existing.mentions:
                    existing.mentions = entity.mentions
                    existing.context.extend(entity.context)
        
        return list(seen.values())

    def merge_entities(
        self,
        entities1: List[ExtractedEntity],
        entities2: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """Merge two lists of entities, combining information."""
        all_entities = entities1 + entities2
        return self._deduplicate_entities(all_entities)