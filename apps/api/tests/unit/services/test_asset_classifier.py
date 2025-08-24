"""Tests for asset classification service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.asset_classifier import AssetClassifier
from app.models import Asset


class TestAssetClassifier:
    """Test suite for asset classification service."""

    def test_classify_by_market_cap_micro(self):
        """Test micro cap classification."""
        result = AssetClassifier.classify_by_market_cap(100_000_000)
        assert result == "micro"

    def test_classify_by_market_cap_small(self):
        """Test small cap classification."""
        result = AssetClassifier.classify_by_market_cap(1_000_000_000)
        assert result == "small"

    def test_classify_by_market_cap_mid(self):
        """Test mid cap classification."""
        result = AssetClassifier.classify_by_market_cap(5_000_000_000)
        assert result == "mid"

    def test_classify_by_market_cap_large(self):
        """Test large cap classification."""
        result = AssetClassifier.classify_by_market_cap(50_000_000_000)
        assert result == "large"

    def test_classify_by_market_cap_mega(self):
        """Test mega cap classification."""
        result = AssetClassifier.classify_by_market_cap(500_000_000_000)
        assert result == "mega"

    def test_classify_by_market_cap_none(self):
        """Test classification with no market cap."""
        result = AssetClassifier.classify_by_market_cap(None)
        assert result is None

    def test_enrich_asset_known_symbol(self):
        """Test enriching asset with known symbol."""
        # Create mock asset
        asset = Mock(spec=Asset)
        asset.symbol = "AAPL"
        asset.market_cap = 3_000_000_000_000
        asset.sector = None
        asset.esg_score = None
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Enrich asset
        enriched = AssetClassifier.enrich_asset(asset, mock_db)
        
        # Verify enrichment
        assert enriched.sector == "Technology"
        assert enriched.industry == "Consumer Electronics"
        assert "consumer_tech" in enriched.tags
        assert enriched.market_cap_category == "mega"
        assert enriched.esg_score == 75
        assert enriched.environmental_score == 70
        assert enriched.social_score == 80
        assert enriched.governance_score == 75

    def test_enrich_asset_unknown_symbol(self):
        """Test enriching asset with unknown symbol."""
        # Create mock asset
        asset = Mock(spec=Asset)
        asset.symbol = "UNKNOWN"
        asset.market_cap = 10_000_000_000
        asset.sector = None
        asset.esg_score = None
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Enrich asset
        enriched = AssetClassifier.enrich_asset(asset, mock_db)
        
        # Verify only market cap classification
        assert enriched.market_cap_category == "large"
        assert enriched.sector is None
        assert enriched.esg_score is None

    def test_enrich_asset_financial_sector(self):
        """Test enriching financial sector asset."""
        # Create mock asset
        asset = Mock(spec=Asset)
        asset.symbol = "JPM"
        asset.market_cap = 400_000_000_000
        asset.sector = None
        asset.esg_score = None
        
        # Create mock session
        mock_db = Mock(spec=Session)
        
        # Enrich asset
        enriched = AssetClassifier.enrich_asset(asset, mock_db)
        
        # Verify enrichment
        assert enriched.sector == "Finance"
        assert enriched.industry == "Banking"
        assert "banking" in enriched.tags
        assert enriched.market_cap_category == "mega"
        assert enriched.esg_score == 70

    def test_bulk_classify_success(self):
        """Test bulk classification of multiple assets."""
        # Create mock assets
        asset1 = Mock(spec=Asset, symbol="AAPL", market_cap=3_000_000_000_000, sector=None, esg_score=None)
        asset2 = Mock(spec=Asset, symbol="MSFT", market_cap=2_500_000_000_000, sector=None, esg_score=None)
        asset3 = Mock(spec=Asset, symbol="GOOGL", market_cap=1_800_000_000_000, sector=None, esg_score=None)
        
        # Create mock session
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.all.return_value = [asset1, asset2, asset3]
        
        # Bulk classify
        result = AssetClassifier.bulk_classify(mock_db)
        
        # Verify results
        assert result["total_assets"] == 3
        assert result["classified"] == 3
        assert result["success"] is True
        mock_db.commit.assert_called_once()

    def test_bulk_classify_with_symbols(self):
        """Test bulk classification with specific symbols."""
        # Create mock assets
        asset1 = Mock(spec=Asset, symbol="AAPL", market_cap=3_000_000_000_000, sector=None, esg_score=None)
        asset2 = Mock(spec=Asset, symbol="MSFT", market_cap=2_500_000_000_000, sector=None, esg_score=None)
        
        # Create mock session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [asset1, asset2]
        
        # Bulk classify specific symbols
        result = AssetClassifier.bulk_classify(mock_db, symbols=["AAPL", "MSFT"])
        
        # Verify results
        assert result["total_assets"] == 2
        assert result["classified"] == 2
        assert result["success"] is True
        mock_query.filter.assert_called_once()

    @patch('app.services.asset_classifier.logger')
    def test_bulk_classify_with_error(self, mock_logger):
        """Test bulk classification with error handling."""
        # Create mock asset that will cause error
        asset = Mock(spec=Asset)
        asset.symbol = Mock(upper=Mock(side_effect=Exception("Test error")))
        
        # Create mock session
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.all.return_value = [asset]
        
        # Bulk classify
        result = AssetClassifier.bulk_classify(mock_db)
        
        # Verify error handling
        assert result["total_assets"] == 1
        assert result["classified"] == 0
        assert result["success"] is False
        mock_logger.error.assert_called_once()

    def test_identify_supply_chain_dependencies_known(self):
        """Test identifying supply chain dependencies for known asset."""
        dependencies = AssetClassifier.identify_supply_chain_dependencies("AAPL")
        
        assert "TSM" in dependencies
        assert "QCOM" in dependencies
        assert len(dependencies) == 5

    def test_identify_supply_chain_dependencies_unknown(self):
        """Test identifying supply chain dependencies for unknown asset."""
        dependencies = AssetClassifier.identify_supply_chain_dependencies("UNKNOWN")
        
        assert dependencies == []

    def test_calculate_volatility_sufficient_data(self):
        """Test volatility calculation with sufficient data."""
        prices = [100, 102, 101, 103, 104, 102, 105, 103, 106, 104] * 5  # 50 prices
        
        volatility = AssetClassifier.calculate_volatility(prices, period=30)
        
        assert volatility is not None
        assert volatility > 0

    def test_calculate_volatility_insufficient_data(self):
        """Test volatility calculation with insufficient data."""
        prices = [100, 102, 101, 103, 104]  # Only 5 prices
        
        volatility = AssetClassifier.calculate_volatility(prices, period=30)
        
        assert volatility is None

    def test_calculate_volatility_empty_data(self):
        """Test volatility calculation with empty data."""
        prices = []
        
        volatility = AssetClassifier.calculate_volatility(prices, period=30)
        
        assert volatility is None

    def test_sector_mappings_completeness(self):
        """Test that sector mappings are properly structured."""
        for symbol, mapping in AssetClassifier.SECTOR_MAPPINGS.items():
            assert "sector" in mapping
            assert "industry" in mapping
            assert "tags" in mapping
            assert isinstance(mapping["tags"], list)
            assert len(mapping["tags"]) > 0

    def test_healthcare_sector_classification(self):
        """Test healthcare sector asset classification."""
        asset = Mock(spec=Asset)
        asset.symbol = "JNJ"
        asset.market_cap = 450_000_000_000
        asset.sector = None
        asset.esg_score = None
        
        mock_db = Mock(spec=Session)
        
        enriched = AssetClassifier.enrich_asset(asset, mock_db)
        
        assert enriched.sector == "Healthcare"
        assert enriched.industry == "Pharmaceuticals"
        assert "pharma" in enriched.tags
        assert enriched.esg_score == 80

    def test_energy_sector_classification(self):
        """Test energy sector asset classification."""
        asset = Mock(spec=Asset)
        asset.symbol = "XOM"
        asset.market_cap = 400_000_000_000
        asset.sector = None
        asset.esg_score = None
        
        mock_db = Mock(spec=Session)
        
        enriched = AssetClassifier.enrich_asset(asset, mock_db)
        
        assert enriched.sector == "Energy"
        assert enriched.industry == "Oil & Gas"
        assert "oil" in enriched.tags
        assert enriched.esg_score == 55  # Lower ESG for energy sector