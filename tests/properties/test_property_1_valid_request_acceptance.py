"""
Property-based test for valid request acceptance.

Feature: kiro-backend, Property 1: Valid Request Acceptance

For any JSON request containing a problem description (10-1000 chars), 
city name (2-100 chars), and optionally valid coordinates (lat: -90 to 90, 
lon: -180 to 180), the Request_Validator should accept and parse the 
request successfully.

Validates: Requirements 1.1
"""

import json
from hypothesis import given, settings, strategies as st
from src.request_validator import RequestValidator


# Custom strategies for valid inputs
problem_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=10,
    max_size=1000
)

city_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=2,
    max_size=100
)

latitude_strategy = st.floats(
    min_value=-90.0,
    max_value=90.0,
    allow_nan=False,
    allow_infinity=False
)

longitude_strategy = st.floats(
    min_value=-180.0,
    max_value=180.0,
    allow_nan=False,
    allow_infinity=False
)


@settings(max_examples=100, deadline=None)
@given(
    problem=problem_strategy,
    city=city_strategy,
    include_coords=st.booleans(),
    lat=latitude_strategy,
    lon=longitude_strategy,
    correlation_id=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_property_1_valid_request_acceptance(
    problem: str,
    city: str,
    include_coords: bool,
    lat: float,
    lon: float,
    correlation_id: str
):
    """
    **Validates: Requirements 1.1**
    
    Property 1: Valid Request Acceptance
    
    For any JSON request containing a problem description (10-1000 chars),
    city name (2-100 chars), and optionally valid coordinates (lat: -90 to 90,
    lon: -180 to 180), the Request_Validator should accept and parse the
    request successfully.
    
    This test verifies that:
    1. All valid requests are accepted by the validator
    2. The validator successfully parses valid request data
    3. Optional coordinates are handled correctly when present or absent
    4. Correlation IDs are properly extracted from headers
    """
    # Arrange: Build request with required fields and optional coordinates
    request_body = {
        "problem": problem,
        "city": city
    }
    
    if include_coords:
        request_body["latitude"] = lat
        request_body["longitude"] = lon
    
    # Build API Gateway event structure
    event = {
        "body": json.dumps(request_body),
        "headers": {}
    }
    
    if correlation_id is not None:
        event["headers"]["x-correlation-id"] = correlation_id
    
    # Act: Validate the request
    validator = RequestValidator()
    result = validator.validate(event)
    
    # Assert: Request should be valid and parsed correctly
    assert result.is_valid, f"Valid request was rejected: {result.error_message}"
    assert result.parsed_data is not None, "Parsed data should not be None for valid requests"
    assert result.error_message is None, "Error message should be None for valid requests"
    
    # Verify parsed data contains expected fields
    assert result.parsed_data["problem"] == problem
    assert result.parsed_data["city"] == city
    
    if include_coords:
        assert result.parsed_data["latitude"] == lat
        assert result.parsed_data["longitude"] == lon
    else:
        assert "latitude" not in result.parsed_data
        assert "longitude" not in result.parsed_data
    
    # Verify correlation_id is included in parsed data
    assert "correlation_id" in result.parsed_data
    if correlation_id is not None:
        assert result.parsed_data["correlation_id"] == correlation_id
    else:
        # Should be None if not provided
        assert result.parsed_data["correlation_id"] is None
