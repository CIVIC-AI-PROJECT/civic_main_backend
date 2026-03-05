"""
Response builder component for the Kiro Backend civic assistant system.

This module constructs JSON responses conforming to the Output_Schema,
including success responses with office recommendations and error responses.
"""

import json
import os
from typing import List, Optional, Dict, Any
import jsonschema

from src.models import Office, Checklist, ConversationScript


class ResponseBuilder:
    """
    Constructs JSON responses conforming to Output_Schema.
    
    Responsibilities:
    - Build success responses with office recommendations
    - Build error responses with descriptive messages
    - Include privacy information block
    - Validate responses against Output_Schema
    - Format distances with units
    """
    
    def __init__(self):
        """Initialize the response builder with Output_Schema."""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            'schemas',
            'output_schema.json'
        )
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def build_success_response(
        self,
        primary_office: Office,
        alternatives: List[Office],
        checklist: Checklist,
        script: ConversationScript,
        bedrock_used: bool,
        correlation_id: str,
        processing_time_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds successful response conforming to Output_Schema.
        
        Args:
            primary_office: Recommended office with distance and explanation
            alternatives: List of alternative offices
            checklist: Documents and preparation steps
            script: Conversation script with opening and follow-ups
            bedrock_used: Whether Bedrock generated content
            correlation_id: Request correlation ID
            processing_time_ms: Optional processing duration
        
        Returns:
            Response dict conforming to Output_Schema
        """
        # Build recommended office object
        recommended_office = {
            "name": primary_office.name,
            "address": primary_office.address,
            "distance_km": primary_office.distance_km if primary_office.distance_km is not None else -1,
            "explanation": primary_office.explanation or "This office handles your request type."
        }
        
        # Add optional fields if present
        if primary_office.phone:
            recommended_office["phone"] = primary_office.phone
        if primary_office.hours:
            recommended_office["hours"] = primary_office.hours
        
        # Build alternatives array
        alternatives_list = []
        for alt in alternatives:
            alt_obj = {
                "name": alt.name,
                "address": alt.address,
                "distance_km": alt.distance_km if alt.distance_km is not None else -1
            }
            if alt.phone:
                alt_obj["phone"] = alt.phone
            if alt.hours:
                alt_obj["hours"] = alt.hours
            alternatives_list.append(alt_obj)
        
        # Build checklist object
        checklist_obj = {
            "documents": checklist.documents,
            "steps": checklist.steps
        }
        
        # Build conversation script object
        script_obj = {
            "opening": script.opening,
            "follow_ups": script.follow_ups
        }
        
        # Build privacy block
        privacy_obj = {
            "stored": [
                "session_id",
                "problem_category",
                "city",
                "timestamp"
            ],
            "not_stored": [
                "problem_description",
                "coordinates",
                "personal_details",
                "documents"
            ]
        }
        
        # Build metadata object
        metadata_obj = {
            "correlation_id": correlation_id,
            "bedrock_used": bedrock_used
        }
        if processing_time_ms is not None:
            metadata_obj["processing_time_ms"] = processing_time_ms
        
        # Construct complete response
        response = {
            "recommended_office": recommended_office,
            "alternatives": alternatives_list,
            "checklist": checklist_obj,
            "conversation_script": script_obj,
            "privacy": privacy_obj,
            "metadata": metadata_obj
        }
        
        # Validate response against schema
        try:
            jsonschema.validate(instance=response, schema=self.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Response validation failed: {e.message}")
        
        return response
    
    def build_error_response(
        self,
        error_type: str,
        message: str,
        correlation_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds error response.
        
        Args:
            error_type: Error category (validation_error, not_found, service_error, internal_error)
            message: Human-readable error description
            correlation_id: Request correlation ID
            details: Optional additional error details
        
        Returns:
            Error response dict
        """
        error_response = {
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {}
            }
        }
        
        # Always include correlation_id in details
        error_response["error"]["details"]["correlation_id"] = correlation_id
        
        return error_response
