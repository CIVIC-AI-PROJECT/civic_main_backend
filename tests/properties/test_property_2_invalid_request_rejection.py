"""
Property-based test for invalid request rejection with descriptive errors.

Feature: kiro-backend, Property 2: Invalid Request Rejection with Descriptive Errors

For any JSON request that fails Input_Schema validation (missing required fields, 
invalid types, out-of-range values), the Request_Validator should return a 
descriptive error message identifying the specific validation failure.

Validates: Requirements 1.4, 2.3, 2.4
"""

import json
from hypothesis import given, settings, strategies as st
from src.request_validator import RequestValidator


# Strategy for generating invalid requests with various failure modes
@st.composite
def invalid_request_strategy(draw):
    """
    Generate invalid requests with different types of validation failures:
    1. Missing required field 'problem'
    2. Missing required field 'city'
    3. Problem too short (< 10 chars)
    4. Problem too long (> 1000 chars)
    5. City too short (< 2 chars)
    6. City too long (> 100 chars)
    7. Latitude out of range (< -90 or > 90)
    8. Longitude out of range (< -180 or > 180)
    9. Invalid field types (non-string for problem/city, non-number for coords)
    10. Additional unexpected fields
    """
    failure_mode = draw(st.sampled_from([
        'missing_problem',
        'missing_city',
        'problem_too_short',
        'problem_too_long',
        'city_too_short',
        'city_too_long',
        'latitude_out_of_range',
        'longitude_out_of_range',
        'invalid_problem_type',
        'invalid_city_type',
        'invalid_latitude_type',
        'invalid_longitude_type',
        'additional_fields'
    ]))
    
    # Base valid request
    request = {
        "problem": draw(st.text(min_size=10, max_size=1000)),
        "city": draw(st.text(min_size=2, max_size=100))
    }
    
    # Apply failure mode
    if failure_mode == 'missing_problem':
        del request['problem']
        expected_error_keywords = ['missing', 'required', 'problem']
    
    elif failure_mode == 'missing_city':
        del request['city']
        expected_error_keywords = ['missing', 'required', 'city']
    
    elif failure_mode == 'problem_too_short':
        request['problem'] = draw(st.text(min_size=0, max_size=9))
        expected_error_keywords = ['problem', 'short', 'length', 'minimum']
    
    elif failure_mode == 'problem_too_long':
        request['problem'] = draw(st.text(min_size=1001, max_size=2000))
        expected_error_keywords = ['problem', 'long', 'length', 'maximum']
    
    elif failure_mode == 'city_too_short':
        request['city'] = draw(st.text(min_size=0, max_size=1))
        expected_error_keywords = ['city', 'short', 'length', 'minimum']
    
    elif failure_mode == 'city_too_long':
        request['city'] = draw(st.text(min_size=101, max_size=200))
        expected_error_keywords = ['city', 'long', 'length', 'maximum']
    
    elif failure_mode == 'latitude_out_of_range':
        # Generate latitude outside valid range
        lat = draw(st.one_of(
            st.floats(min_value=-1000, max_value=-90.1),
            st.floats(min_value=90.1, max_value=1000)
        ))
        request['latitude'] = lat
        expected_error_keywords = ['latitude', 'range', '-90', '90']
    
    elif failure_mode == 'longitude_out_of_range':
        # Generate longitude outside valid range
        lon = draw(st.one_of(
            st.floats(min_value=-1000, max_value=-180.1),
            st.floats(min_value=180.1, max_value=1000)
        ))
        request['longitude'] = lon
        expected_error_keywords = ['longitude', 'range', '-180', '180']
    
    elif failure_mode == 'invalid_problem_type':
        request['problem'] = draw(st.one_of(
            st.integers(),
            st.booleans(),
            st.lists(st.text()),
            st.none()
        ))
        expected_error_keywords = ['problem', 'type', 'string']
    
    elif failure_mode == 'invalid_city_type':
        request['city'] = draw(st.one_of(
            st.integers(),
            st.booleans(),
            st.lists(st.text()),
            st.none()
        ))
        expected_error_keywords = ['city', 'type', 'string']
    
    elif failure_mode == 'invalid_latitude_type':
        request['latitude'] = draw(st.one_of(
            st.text(),
            st.booleans(),
            st.lists(st.integers())
        ))
        expected_error_keywords = ['latitude', 'type', 'number']
    
    elif failure_mode == 'invalid_longitude_type':
        request['longitude'] = draw(st.one_of(
            st.text(),
            st.booleans(),
            st.lists(st.integers())
        ))
        expected_error_keywords = ['longitude', 'type', 'number']
    
    elif failure_mode == 'additional_fields':
        # Add unexpected fields
        request['unexpected_field'] = draw(st.text())
        request['another_field'] = draw(st.integers())
        expected_error_keywords = ['additional', 'unexpected', 'field']
    
    return {
        'request': request,
        'failure_mode': failure_mode,
        'expected_error_keywords': expected_error_keywords
    }


@settings(max_examples=100, deadline=None)
@given(invalid_data=invalid_request_strategy())
def test_property_2_invalid_request_rejection(invalid_data):
    """
    **Validates: Requirements 1.4, 2.3, 2.4**
    
    Property 2: Invalid Request Rejection with Descriptive Errors
    
    For any JSON request that fails Input_Schema validation (missing required fields,
    invalid types, out-of-range values), the Request_Validator should return a
    descriptive error message identifying the specific validation failure.
    
    This test verifies that:
    1. Invalid requests are rejected by the validator
    2. The validator returns descriptive error messages
    3. Error messages identify the specific validation failure
    4. All types of validation failures are properly detected
    """
    # Arrange: Build API Gateway event with invalid request
    request = invalid_data['request']
    failure_mode = invalid_data['failure_mode']
    expected_keywords = invalid_data['expected_error_keywords']
    
    event = {
        "body": json.dumps(request),
        "headers": {}
    }
    
    # Act: Validate the invalid request
    validator = RequestValidator()
    result = validator.validate(event)
    
    # Assert: Request should be rejected
    assert not result.is_valid, (
        f"Invalid request was accepted (failure_mode: {failure_mode}). "
        f"Request: {request}"
    )
    
    # Assert: Error message should be present and descriptive
    assert result.error_message is not None, (
        f"Error message is missing for invalid request (failure_mode: {failure_mode})"
    )
    assert len(result.error_message) > 0, (
        f"Error message is empty for invalid request (failure_mode: {failure_mode})"
    )
    
    # Assert: Error message should be descriptive (contain relevant keywords)
    error_message_lower = result.error_message.lower()
    keyword_found = any(
        keyword.lower() in error_message_lower 
        for keyword in expected_keywords
    )
    assert keyword_found, (
        f"Error message is not descriptive enough for failure_mode '{failure_mode}'. "
        f"Expected one of {expected_keywords} in error message: '{result.error_message}'"
    )
    
    # Assert: Parsed data should be None for invalid requests
    assert result.parsed_data is None, (
        f"Parsed data should be None for invalid requests (failure_mode: {failure_mode})"
    )
    
    # Assert: Error field should be identified when applicable
    # (Some validation errors may not have a specific field, like malformed JSON)
    if failure_mode in ['missing_problem', 'problem_too_short', 'problem_too_long', 
                        'invalid_problem_type']:
        assert result.error_field is not None, (
            f"Error field should be identified for {failure_mode}"
        )
        assert 'problem' in str(result.error_field).lower(), (
            f"Error field should reference 'problem' for {failure_mode}, "
            f"got: {result.error_field}"
        )
    
    elif failure_mode in ['missing_city', 'city_too_short', 'city_too_long', 
                          'invalid_city_type']:
        assert result.error_field is not None, (
            f"Error field should be identified for {failure_mode}"
        )
        assert 'city' in str(result.error_field).lower(), (
            f"Error field should reference 'city' for {failure_mode}, "
            f"got: {result.error_field}"
        )
    
    elif failure_mode in ['latitude_out_of_range', 'invalid_latitude_type']:
        assert result.error_field is not None, (
            f"Error field should be identified for {failure_mode}"
        )
        assert 'latitude' in str(result.error_field).lower(), (
            f"Error field should reference 'latitude' for {failure_mode}, "
            f"got: {result.error_field}"
        )
    
    elif failure_mode in ['longitude_out_of_range', 'invalid_longitude_type']:
        assert result.error_field is not None, (
            f"Error field should be identified for {failure_mode}"
        )
        assert 'longitude' in str(result.error_field).lower(), (
            f"Error field should reference 'longitude' for {failure_mode}, "
            f"got: {result.error_field}"
        )


# Additional test for malformed JSON (not covered by the composite strategy)
@settings(max_examples=50, deadline=None)
@given(
    malformed_json=st.one_of(
        st.just('{"problem": "test", "city": "test"'),  # Missing closing brace
        st.just('{"problem": "test" "city": "test"}'),  # Missing comma
        st.just('{problem: "test", city: "test"}'),     # Unquoted keys
        st.just('{"problem": "test", city: }'),         # Trailing comma
        st.just('not valid json at all'),               # Plain text
    )
)
def test_property_2_malformed_json_rejection(malformed_json):
    """
    **Validates: Requirements 1.4, 2.3, 2.4**
    
    Property 2 (Malformed JSON variant): Invalid Request Rejection
    
    For any malformed JSON in the request body, the Request_Validator should
    return a descriptive error message indicating the JSON parsing failure or
    schema validation failure.
    """
    # Arrange: Build event with malformed JSON
    event = {
        "body": malformed_json,
        "headers": {}
    }
    
    # Act: Validate the request
    validator = RequestValidator()
    result = validator.validate(event)
    
    # Assert: Request should be rejected
    assert not result.is_valid, (
        f"Malformed JSON was accepted: {malformed_json}"
    )
    
    # Assert: Error message should be present and descriptive
    assert result.error_message is not None
    assert len(result.error_message) > 0
    
    # Assert: Parsed data should be None
    assert result.parsed_data is None


# Test for empty body
def test_property_2_empty_body_rejection():
    """
    **Validates: Requirements 1.4, 2.3, 2.4**
    
    Property 2 (Empty body variant): Invalid Request Rejection
    
    For an empty request body, the Request_Validator should return a
    descriptive error message.
    """
    # Arrange: Build event with empty body
    event = {
        "body": "",
        "headers": {}
    }
    
    # Act: Validate the request
    validator = RequestValidator()
    result = validator.validate(event)
    
    # Assert: Request should be rejected
    assert not result.is_valid
    
    # Assert: Error message should be descriptive
    assert result.error_message is not None
    assert 'empty' in result.error_message.lower() or 'body' in result.error_message.lower()
    
    # Assert: Parsed data should be None
    assert result.parsed_data is None
