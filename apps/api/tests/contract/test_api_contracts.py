"""
Contract tests to ensure frontend-backend API compatibility.
These tests verify that API responses match expected schemas.
"""

from datetime import date
import pytest

from app.schemas.index import IndexCurrentResponse, SimulationResponse


@pytest.mark.contract
@pytest.mark.critical
class TestAPIContracts:
    """Ensure API contracts match frontend expectations."""

    def test_index_current_response_contract(self):
        """Test index current response schema."""
        response_data = {
            "date": date.today(),
            "allocations": [
                {
                    "symbol": "AAPL",
                    "weight": 0.15,
                    "name": "Apple Inc.",
                    "sector": "Technology"
                }
            ],
            "total_assets": 1
        }
        
        # Validate against schema
        response = IndexCurrentResponse(**response_data)
        assert response.date == date.today()
        assert len(response.allocations) == 1
        assert response.allocations[0].symbol == "AAPL"

    def test_simulation_response_contract(self):
        """Test simulation response schema."""
        response_data = {
            "start_date": date(2023, 1, 1),
            "end_date": date(2023, 12, 31),
            "start_value": 100.0,
            "end_value": 125.5,
            "amount_initial": 10000.0,
            "amount_final": 12550.0,
            "roi_pct": 25.5,
            "currency": "USD",
            "series": [
                {"date": date(2023, 1, 1), "value": 100.0},
                {"date": date(2023, 12, 31), "value": 125.5}
            ]
        }
        
        # Validate against schema
        response = SimulationResponse(**response_data)
        assert response.roi_pct == 25.5
        assert response.currency == "USD"
        assert len(response.series) == 2