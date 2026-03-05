"""
Unit tests for RequestValidator component.

Tests cover:
- Valid requests with all fields
- Valid requests with optional fields omitted
- Missing required fields
- Out-of-range coordinates
- Malformed JSON
- Wrong field types
- Correlation ID extraction
"""

import json
import pytest
from src.request_validator import RequestValidator


class TestRequestValidator:
    """Test suite for RequestValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = RequestValidator()
    
    def test_valid_request_with_all_fields(self):
        """Test validation of a complete valid request with all fields."""
        event = {
            'body': json.dumps({
                'problem': 'I need to renew my driver license',
                'city': 'Seattle',
                'latitude': 47.6062,
                'longitude': -122.3321
            }),
            'headers': {'x-correlation-id': 'test-123'}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is True
        assert result.parsed_data is not None
        assert result.parsed_data['problem'] == 'I need to renew my driver license'
        assert result.parsed_data['city'] == 'Seattle'
        assert result.parsed_data['latitude'] == 47.6062
        assert result.parsed_data['longitude'] == -122.3321
        assert result.parsed_data['correlation_id'] == 'test-123'
        assert result.error_message is None
    
    def test_valid_request_without_coordinates(self):
        """Test validation of a valid request with only required fields."""
        event = {
            'body': json.dumps({
                'problem': 'I need a building permit for my deck',
                'city': 'Portland'
            }),
            'headers': {'x-correlation-id': 'test-456'}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is True
        assert result.parsed_data is not None
        assert result.parsed_data['problem'] == 'I need a building permit for my deck'
        assert result.parsed_data['city'] == 'Portland'
        assert 'latitude' not in result.parsed_data
        assert 'longitude' not in result.parsed_data
        assert result.parsed_data['correlation_id'] == 'test-456'
    
    def test_valid_request_with_only_latitude(self):
        """Test validation with only latitude provided (longitude optional)."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with property taxes',
                'city': 'Austin',
                'latitude': 30.2672
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is True
        assert result.parsed_data['latitude'] == 30.2672
        assert 'longitude' not in result.parsed_data
    
    def test_missing_required_field_problem(self):
        """Test validation failure when 'problem' field is missing."""
        event = {
            'body': json.dumps({
                'city': 'Seattle'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'problem' in result.error_message.lower()
        assert result.error_field == 'problem'
    
    def test_missing_required_field_city(self):
        """Test validation failure when 'city' field is missing."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with taxes'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'city' in result.error_message.lower()
        assert result.error_field == 'city'
    
    def test_problem_too_short(self):
        """Test validation failure when problem description is too short."""
        event = {
            'body': json.dumps({
                'problem': 'Help',  # Less than 10 characters
                'city': 'Seattle'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert result.error_message is not None
    
    def test_problem_too_long(self):
        """Test validation failure when problem description is too long."""
        event = {
            'body': json.dumps({
                'problem': 'x' * 1001,  # More than 1000 characters
                'city': 'Seattle'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert result.error_message is not None
    
    def test_city_too_short(self):
        """Test validation failure when city name is too short."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'A'  # Less than 2 characters
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert result.error_message is not None
    
    def test_latitude_out_of_range_high(self):
        """Test validation failure when latitude is above 90."""
        event = {
            'body': json.dumps({
                'problem': 'I need a business license',
                'city': 'Seattle',
                'latitude': 91.0
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'latitude' in result.error_message.lower()
        assert result.error_field == 'latitude'
    
    def test_latitude_out_of_range_low(self):
        """Test validation failure when latitude is below -90."""
        event = {
            'body': json.dumps({
                'problem': 'I need a business license',
                'city': 'Seattle',
                'latitude': -91.0
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'latitude' in result.error_message.lower()
        assert result.error_field == 'latitude'
    
    def test_longitude_out_of_range_high(self):
        """Test validation failure when longitude is above 180."""
        event = {
            'body': json.dumps({
                'problem': 'I need a business license',
                'city': 'Seattle',
                'longitude': 181.0
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'longitude' in result.error_message.lower()
        assert result.error_field == 'longitude'
    
    def test_longitude_out_of_range_low(self):
        """Test validation failure when longitude is below -180."""
        event = {
            'body': json.dumps({
                'problem': 'I need a business license',
                'city': 'Seattle',
                'longitude': -181.0
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'longitude' in result.error_message.lower()
        assert result.error_field == 'longitude'
    
    def test_malformed_json(self):
        """Test validation failure with malformed JSON."""
        event = {
            'body': '{invalid json}',
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'json' in result.error_message.lower()
        assert result.error_field == 'body'
    
    def test_empty_body(self):
        """Test validation failure with empty request body."""
        event = {
            'body': '',
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'empty' in result.error_message.lower()
        assert result.error_field == 'body'
    
    def test_wrong_field_type_problem(self):
        """Test validation failure when problem is not a string."""
        event = {
            'body': json.dumps({
                'problem': 12345,  # Should be string
                'city': 'Seattle'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert result.error_message is not None
    
    def test_wrong_field_type_coordinates(self):
        """Test validation failure when coordinates are not numbers."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle',
                'latitude': 'not a number'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert result.error_message is not None
    
    def test_additional_unexpected_fields(self):
        """Test validation failure with additional unexpected fields."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle',
                'unexpected_field': 'should not be here'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is False
        assert 'unexpected' in result.error_message.lower() or 'additional' in result.error_message.lower()
    
    def test_correlation_id_extraction_lowercase(self):
        """Test correlation ID extraction from lowercase header."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle'
            }),
            'headers': {'x-correlation-id': 'abc-def-123'}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is True
        assert result.parsed_data['correlation_id'] == 'abc-def-123'
    
    def test_correlation_id_extraction_uppercase(self):
        """Test correlation ID extraction from uppercase header."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle'
            }),
            'headers': {'X-Correlation-Id': 'xyz-789'}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is True
        assert result.parsed_data['correlation_id'] == 'xyz-789'
    
    def test_missing_correlation_id(self):
        """Test that validation succeeds even without correlation ID."""
        event = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle'
            }),
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is True
        assert result.parsed_data['correlation_id'] is None
    
    def test_body_as_dict(self):
        """Test validation when body is already a dict (not JSON string)."""
        event = {
            'body': {
                'problem': 'I need help with permits',
                'city': 'Seattle'
            },
            'headers': {}
        }
        
        result = self.validator.validate(event)
        
        assert result.is_valid is True
        assert result.parsed_data['problem'] == 'I need help with permits'
    
    def test_boundary_values_latitude(self):
        """Test validation with boundary values for latitude."""
        # Test minimum valid latitude
        event_min = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle',
                'latitude': -90.0
            }),
            'headers': {}
        }
        result_min = self.validator.validate(event_min)
        assert result_min.is_valid is True
        
        # Test maximum valid latitude
        event_max = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle',
                'latitude': 90.0
            }),
            'headers': {}
        }
        result_max = self.validator.validate(event_max)
        assert result_max.is_valid is True
    
    def test_boundary_values_longitude(self):
        """Test validation with boundary values for longitude."""
        # Test minimum valid longitude
        event_min = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle',
                'longitude': -180.0
            }),
            'headers': {}
        }
        result_min = self.validator.validate(event_min)
        assert result_min.is_valid is True
        
        # Test maximum valid longitude
        event_max = {
            'body': json.dumps({
                'problem': 'I need help with permits',
                'city': 'Seattle',
                'longitude': 180.0
            }),
            'headers': {}
        }
        result_max = self.validator.validate(event_max)
        assert result_max.is_valid is True
