"""
Unit tests for OfficeRanker component.

Tests cover:
- Ranking with 4+ offices
- Ranking with fewer than 4 offices
- Ranking with equal distances
- Ranking with missing distances
- Category relevance boost
"""

import pytest
from src.office_ranker import OfficeRanker
from src.models import Office, RankedOffices


@pytest.fixture
def sample_offices():
    """Create sample offices for testing."""
    return [
        Office(
            office_id="office-1",
            office_type="city_hall",
            name="City Hall Downtown",
            address="100 Main St",
            latitude=47.6062,
            longitude=-122.3321,
            city="Seattle",
            category_tags=["permits", "licenses"]
        ),
        Office(
            office_id="office-2",
            office_type="dmv",
            name="DMV North",
            address="200 North Ave",
            latitude=47.6205,
            longitude=-122.3493,
            city="Seattle",
            category_tags=["licenses", "transportation"]
        ),
        Office(
            office_id="office-3",
            office_type="tax_office",
            name="Tax Office South",
            address="300 South St",
            latitude=47.5952,
            longitude=-122.3321,
            city="Seattle",
            category_tags=["taxes", "property"]
        ),
        Office(
            office_id="office-4",
            office_type="city_hall",
            name="City Hall East",
            address="400 East Blvd",
            latitude=47.6062,
            longitude=-122.3100,
            city="Seattle",
            category_tags=["permits", "business"]
        ),
        Office(
            office_id="office-5",
            office_type="health_dept",
            name="Health Department",
            address="500 Health Way",
            latitude=47.6150,
            longitude=-122.3400,
            city="Seattle",
            category_tags=["health", "vital_records"]
        )
    ]


def test_rank_with_four_or_more_offices(sample_offices):
    """Test ranking with 4+ offices returns primary and 3 alternatives."""
    ranker = OfficeRanker()
    distances = [2.5, 1.0, 3.0, 4.0, 2.0]
    
    result = ranker.rank(sample_offices, distances, "licenses")
    
    # Should have primary and 3 alternatives
    assert result.primary is not None
    assert len(result.alternatives) == 3
    
    # Primary should be the closest with category match (office-2: 1.0 km + 10 bonus)
    assert result.primary.office_id == "office-2"
    assert result.primary.distance_km == 1.0
    
    # Alternatives should be next 3 best
    alt_ids = [alt.office_id for alt in result.alternatives]
    assert len(alt_ids) == 3


def test_rank_with_fewer_than_four_offices():
    """Test ranking with fewer than 4 offices returns all available."""
    ranker = OfficeRanker()
    offices = [
        Office(
            office_id="office-1",
            office_type="city_hall",
            name="City Hall",
            address="100 Main St",
            latitude=47.6062,
            longitude=-122.3321,
            city="Seattle",
            category_tags=["permits"]
        ),
        Office(
            office_id="office-2",
            office_type="dmv",
            name="DMV",
            address="200 North Ave",
            latitude=47.6205,
            longitude=-122.3493,
            city="Seattle",
            category_tags=["licenses"]
        )
    ]
    distances = [2.5, 1.0]
    
    result = ranker.rank(offices, distances, "licenses")
    
    # Should have primary and 1 alternative (only 2 offices total)
    assert result.primary is not None
    assert len(result.alternatives) == 1
    
    # Primary should be the closest with category match
    assert result.primary.office_id == "office-2"


def test_rank_with_equal_distances(sample_offices):
    """Test ranking with equal distances uses category relevance as tiebreaker."""
    ranker = OfficeRanker()
    # All same distance
    distances = [2.0, 2.0, 2.0, 2.0, 2.0]
    
    result = ranker.rank(sample_offices, distances, "permits")
    
    # Primary should have category match (permits)
    assert "permits" in result.primary.category_tags
    assert result.primary.distance_km == 2.0


def test_rank_with_missing_distances(sample_offices):
    """Test ranking without distances uses only category relevance."""
    ranker = OfficeRanker()
    
    result = ranker.rank(sample_offices, None, "taxes")
    
    # Should still return primary and alternatives
    assert result.primary is not None
    assert len(result.alternatives) == 3
    
    # Primary should have category match
    assert "taxes" in result.primary.category_tags
    
    # All offices should have None distance
    assert result.primary.distance_km is None
    for alt in result.alternatives:
        assert alt.distance_km is None


def test_category_relevance_boost(sample_offices):
    """Test that category match provides +10 score boost."""
    ranker = OfficeRanker()
    # Office-3 is closer (1.0 km) but doesn't match category
    # Office-2 is farther (5.0 km) but matches category (5.0 + 10 = 5.0 score vs 1.0)
    distances = [10.0, 5.0, 1.0, 8.0, 7.0]
    
    result = ranker.rank(sample_offices, distances, "licenses")
    
    # Office-2 should win due to category boost despite being farther than office-3
    # Score for office-2: -5.0 + 10 = 5.0
    # Score for office-3: -1.0 + 0 = -1.0
    assert result.primary.office_id == "office-2"


def test_rank_empty_offices_raises_error():
    """Test that ranking empty office list raises ValueError."""
    ranker = OfficeRanker()
    
    with pytest.raises(ValueError, match="Cannot rank empty office list"):
        ranker.rank([], [], "permits")


def test_rank_mismatched_distances_raises_error(sample_offices):
    """Test that mismatched distances length raises ValueError."""
    ranker = OfficeRanker()
    distances = [1.0, 2.0]  # Only 2 distances for 5 offices
    
    with pytest.raises(ValueError, match="Distances length .* must match offices length"):
        ranker.rank(sample_offices, distances, "permits")


def test_rank_single_office():
    """Test ranking with single office returns it as primary with no alternatives."""
    ranker = OfficeRanker()
    offices = [
        Office(
            office_id="office-1",
            office_type="city_hall",
            name="City Hall",
            address="100 Main St",
            latitude=47.6062,
            longitude=-122.3321,
            city="Seattle",
            category_tags=["permits"]
        )
    ]
    distances = [2.5]
    
    result = ranker.rank(offices, distances, "permits")
    
    # Should have primary but no alternatives
    assert result.primary is not None
    assert result.primary.office_id == "office-1"
    assert len(result.alternatives) == 0


def test_rank_preserves_office_data(sample_offices):
    """Test that ranking preserves all office data fields."""
    ranker = OfficeRanker()
    # Add optional fields to first office
    sample_offices[0].hours = "Mon-Fri 9am-5pm"
    sample_offices[0].phone = "(206) 555-0100"
    distances = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    result = ranker.rank(sample_offices, distances, "permits")
    
    # Primary should preserve all fields
    assert result.primary.hours == "Mon-Fri 9am-5pm"
    assert result.primary.phone == "(206) 555-0100"
    assert result.primary.name == "City Hall Downtown"
    assert result.primary.address == "100 Main St"


def test_rank_no_category_match(sample_offices):
    """Test ranking when no offices match the category."""
    ranker = OfficeRanker()
    distances = [2.5, 1.0, 3.0, 4.0, 2.0]
    
    # Use category that doesn't match any office
    result = ranker.rank(sample_offices, distances, "nonexistent_category")
    
    # Should still rank by distance only
    assert result.primary is not None
    # Closest office (office-2 at 1.0 km) should be primary
    assert result.primary.office_id == "office-2"
    assert result.primary.distance_km == 1.0
