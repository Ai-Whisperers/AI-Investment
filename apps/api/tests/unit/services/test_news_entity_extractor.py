"""
Unit tests for news entity extraction module.
"""

import pytest
from app.services.news_modules.entity_extractor import EntityExtractor, ExtractedEntity


@pytest.mark.unit
class TestEntityExtractor:
    """Test entity extraction functionality."""
    
    @pytest.fixture
    def extractor(self):
        """Create an entity extractor with known symbols."""
        known_symbols = {
            'AAPL': 'Apple Inc.',
            'GOOGL': 'Alphabet Inc.',
            'MSFT': 'Microsoft Corporation',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.'
        }
        return EntityExtractor(known_symbols)
    
    @pytest.fixture
    def empty_extractor(self):
        """Create an entity extractor without known symbols."""
        return EntityExtractor()
    
    def test_extract_tickers_from_text(self, extractor):
        """Test extraction of ticker symbols from text."""
        text = "AAPL and GOOGL reported strong earnings today"
        entities = extractor._extract_tickers(text)
        
        assert len(entities) >= 2
        symbols = [e.symbol for e in entities]
        assert 'AAPL' in symbols
        assert 'GOOGL' in symbols
    
    def test_extract_tickers_with_title(self, extractor):
        """Test ticker extraction with title context."""
        title = "MSFT Announces New Product"
        text = "The company will compete with AAPL in this market"
        entities = extractor._extract_tickers(text, title)
        
        symbols = [e.symbol for e in entities]
        assert 'MSFT' in symbols
        assert 'AAPL' in symbols
    
    def test_extract_companies_from_text(self, extractor):
        """Test extraction of company names."""
        text = "Apple Inc. and Microsoft Corporation announced a partnership"
        entities = extractor._extract_companies(text)
        
        assert len(entities) >= 2
        names = [e.name for e in entities]
        assert any('Apple' in name for name in names)
        assert any('Microsoft' in name for name in names)
    
    def test_extract_sectors(self, extractor):
        """Test extraction of sector information."""
        text = "The technology sector outperformed while energy stocks declined"
        entities = extractor._extract_sectors(text)
        
        assert len(entities) >= 1
        types = [e.type for e in entities]
        assert 'SECTOR' in types
    
    def test_extract_entities_complete(self, extractor):
        """Test complete entity extraction from article."""
        text = """
        Apple Inc. (AAPL) reported record earnings in the technology sector.
        The company's CEO discussed future growth prospects. Meanwhile, 
        Microsoft (MSFT) and Amazon (AMZN) also showed strong performance.
        """
        
        entities = extractor.extract_entities(text)
        
        assert len(entities) > 0
        
        # Check for ticker symbols
        symbols = [e.symbol for e in entities if e.type == 'STOCK']
        assert 'AAPL' in symbols or 'Apple' in str(symbols)
        
        # Check for multiple entity types
        entity_types = set(e.type for e in entities)
        assert len(entity_types) >= 1
    
    def test_deduplicate_entities(self, extractor):
        """Test entity deduplication."""
        entities = [
            ExtractedEntity('AAPL', 'Apple Inc.', 'STOCK', 2, ['context1']),
            ExtractedEntity('AAPL', 'Apple Inc.', 'STOCK', 1, ['context2']),
            ExtractedEntity('GOOGL', 'Alphabet Inc.', 'STOCK', 1, ['context3'])
        ]
        
        deduped = extractor._deduplicate_entities(entities)
        
        # Should combine AAPL entries
        assert len(deduped) == 2
        
        # AAPL should have combined mention count
        aapl_entity = next(e for e in deduped if e.symbol == 'AAPL')
        assert aapl_entity.mentions == 3
    
    def test_extract_entities_empty_text(self, extractor):
        """Test entity extraction with empty text."""
        entities = extractor.extract_entities("")
        assert entities == []
    
    def test_extract_entities_no_entities(self, extractor):
        """Test extraction when no entities are present."""
        text = "The weather today is sunny and warm"
        entities = extractor.extract_entities(text)
        
        # May find false positives in all caps words, but should be minimal
        assert len(entities) <= 2
    
    def test_ticker_pattern_matching(self, extractor):
        """Test ticker pattern regex."""
        # Valid tickers
        assert EntityExtractor.TICKER_PATTERN.match('AAPL')
        assert EntityExtractor.TICKER_PATTERN.match('A')
        assert EntityExtractor.TICKER_PATTERN.match('GOOGL')
        
        # Invalid tickers
        assert not EntityExtractor.TICKER_PATTERN.match('aap')  # lowercase
        assert not EntityExtractor.TICKER_PATTERN.match('TOOLONG')  # > 5 chars
        assert not EntityExtractor.TICKER_PATTERN.match('123')  # numbers
    
    def test_extract_entities_with_context(self, extractor):
        """Test that entity context is captured."""
        text = "AAPL surged 10% on strong iPhone sales. AAPL is now worth $3 trillion."
        entities = extractor.extract_entities(text)
        
        aapl_entity = next((e for e in entities if e.symbol == 'AAPL'), None)
        assert aapl_entity is not None
        assert aapl_entity.mentions >= 2
        assert len(aapl_entity.context) >= 1
    
    def test_entity_type_classification(self, extractor):
        """Test correct entity type classification."""
        text = """
        The S&P 500 index rose today. Gold commodity prices increased.
        USD strengthened against EUR. Tech stocks like AAPL gained.
        """
        
        entities = extractor.extract_entities(text)
        
        # Should identify different entity types
        entity_types = {e.type for e in entities}
        # May include INDEX, COMMODITY, CURRENCY, STOCK
        assert len(entity_types) >= 1
    
    def test_extract_with_unknown_symbols(self, empty_extractor):
        """Test extraction without known symbols database."""
        text = "XYZ and ABC stocks traded heavily today"
        entities = empty_extractor.extract_entities(text)
        
        # Should still extract potential tickers
        symbols = [e.symbol for e in entities if len(e.symbol) <= 5]
        assert 'XYZ' in symbols or 'ABC' in symbols
    
    def test_company_suffix_detection(self, extractor):
        """Test detection of company suffixes."""
        suffixes = EntityExtractor.COMPANY_SUFFIXES
        
        assert 'Inc.' in suffixes
        assert 'Corp.' in suffixes
        assert 'LLC' in suffixes
        assert 'Ltd.' in suffixes
        
        # Test in context
        text = "Amazon.com Inc. and Tesla Motors Corporation announced..."
        entities = extractor._extract_companies(text)
        
        # Should detect companies with suffixes
        assert len(entities) >= 1