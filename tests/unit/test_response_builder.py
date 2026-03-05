"""
Unit tests for ResponseBuilder component.

Tests the construction of success and error responses, schema validation,
privacy block inclusion, and proper formatting of all response fields.
"""

import pytest
import jsonschema
from src.response_builder import ResponseBuilder
from src.models import Office, Checklist, ConversationScript


class TestResponseBuilder:
    """Test suite for ResponseBuilder class."""
    
    @pytest.fixture
    def builder(self):
        """Create ResponseBuilder instance."""
        return ResponseBuilder()
    
    @pytest.fixture
    def sample_primary_office(self):
        """Create sample primary office with all fields."""
        return Office(
            office_id="office-123",
            office_type="dmv",
            name="Seattle DMV - Downtown",
            address="123 Main St, Seattle, WA 98101",
            latitude=47.6062,
            longitude=-122.3321,
            city="Seattle",
            category_tags=["licenses", "transportation"],
            hours="Mon-Fri 8am-5pm",
            phone="(206) 555-0100",
            distance_km=2.3,
            explanation="• This DMV location is closest to you (2.3 km away)\n• Handles all driver's license services\n• Please verify current wait times at the counter"
        )
    
    @pytest.fixture
    def sample_alternatives(self):
        """Create sample alternative offices."""
        return [
            Office(
                office_id="office-456",
                office_type="dmv",
                name="Seattle DMV - North",
                address="456 North Ave, Seattle, WA 98103",
                latitude=47.6205,
                longitude=-122.3493,
                city="Seattle",
                category_tags=["licenses", "transportation"],
                hours="Mon-Fri 8am-5pm",
                phone="(206) 555-0101",
                distance_km=5.7
            )
        ]