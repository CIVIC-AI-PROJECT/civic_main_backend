"""
Request validation component for the Kiro Backend civic assistant system.

This module provides the RequestValidator class that validates incoming API Gateway
events against the Input_Schema, ensuring all requests meet the required format and
constraints before processing.
"""

import json
import os
from typing import Dict, Any
import jsonschema
from jsonschema import ValidationError as JsonSchemaValidationError

from src.models import ValidationResult


class RequestValidator:
    """
    Validates incoming API Gateway requests against the Input_Schema.
    
    This validator ensures that:
    - JSON body is properly formatted
    - Required fields (problem, city) are present
    - Optional fields (latitude, longitude) are within valid ranges
    - No additional unexpected fields are present
    - Correlation ID is extracted from headers
    """
    
    def __init__(self):
        """Initialize the validator with the Input_Schema."""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            'schemas',
            'input_schema.json'
        )
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def validate(self, event: Dict[str, Any]) -> ValidationResult:
        """
        Validates API Gateway event against Input_Schema.
        
        Args:
            event: API Gateway event dictionary containing:
                - body: JSON string with request data
                - headers: Dictionary with request headers (including correlation_id)
        
        Returns:
            ValidationResult with:
                - is_valid: True if validation passed
                - parsed_data: Dictionary with validated request data and correlation_id
                - error_message: Description of validation failure (if any)
                - error_field: Specific field that failed validation (if applicable)
        
        Examples:
            >>> validator = RequestValidator()
            >>> event = {
            ...     'body': '{"problem": "Need building permit", "city": "Seattle"}',
            ...     'headers': {'x-correlation-id': 'abc-123'}
            ... }
            >>> result = validator.validate(event)
            >>> result.is_valid
            True
        """
        # Extract correlation_id from headers
        headers = event.get('headers', {})
        correlation_id = headers.get('x-correlation-id') or headers.get('X-Correlation-Id')
        
        # Parse JSON body
        body = event.get('body', '')
        if not body:
            return ValidationResult(
                is_valid=False,
                error_message="Request body is empty",
                error_field="body"
            )
        
        try:
            request_data = json.loads(body) if isinstance(body, str) else body
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Malformed JSON: {str(e)}",
                error_field="body"
            )
        
        # Validate against schema
        try:
            jsonschema.validate(instance=request_data, schema=self.schema)
        except JsonSchemaValidationError as e:
            # Extract field name from validation error path
            error_field = e.path[0] if e.path else None
            
            # Create descriptive error message
            if 'required' in e.message.lower():
                missing_field = e.message.split("'")[1] if "'" in e.message else "unknown"
                error_message = f"Missing required field: {missing_field}"
                error_field = missing_field
            elif error_field == 'latitude':
                error_message = "Latitude must be between -90 and 90 degrees"
            elif error_field == 'longitude':
                error_message = "Longitude must be between -180 and 180 degrees"
            elif 'additionalProperties' in e.message:
                error_message = "Request contains unexpected fields"
            else:
                error_message = e.message
            
            return ValidationResult(
                is_valid=False,
                error_message=error_message,
                error_field=str(error_field) if error_field else None
            )
        
        # Add correlation_id to parsed data
        parsed_data = {
            **request_data,
            'correlation_id': correlation_id
        }
        
        return ValidationResult(
            is_valid=True,
            parsed_data=parsed_data
        )
