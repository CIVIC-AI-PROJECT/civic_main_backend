"""
Problem classification component for the Kiro Backend civic assistant system.

This module categorizes user problem descriptions into predefined categories
using rule-based keyword matching with optional Bedrock AI enhancement.
"""

import re
from typing import Optional
import boto3
from botocore.exceptions import ClientError


class ProblemClassifier:
    """
    Categorizes user problem descriptions into predefined categories.
    
    Categories:
    - permits: Building permits, construction permits
    - licenses: Driver's licenses, business licenses, professional licenses
    - taxes: Property taxes, business taxes, tax payments
    - vital_records: Birth certificates, death certificates, marriage licenses
    - property: Property records, deeds, assessments
    - business: Business registration, permits, compliance
    - health: Health services, inspections, permits
    - transportation: Transit, parking, vehicle registration
    - general: Default category for unclear requests
    
    Strategy:
    1. Primary: Use Bedrock for AI-based classification (if available)
    2. Fallback: Rule-based keyword matching
    3. Default: Return "general" when confidence is low
    """
    
    CATEGORIES = [
        'permits',
        'licenses',
        'taxes',
        'vital_records',
        'property',
        'business',
        'health',
        'transportation',
        'general'
    ]
    
    # Rule-based keyword patterns for fallback classification
    KEYWORD_PATTERNS = {
        'permits': [
            r'\b(building|construction|renovation|deck|fence|permit)\b',
            r'\b(zoning|variance|demolition)\b'
        ],
        'licenses': [
            r'\b(driver|license|licence|dmv|id card)\b',
            r'\b(renew|renewal|professional license)\b'
        ],
        'taxes': [
            r'\b(tax|taxes|property tax|business tax|payment)\b',
            r'\b(assessment|levy|revenue)\b'
        ],
        'vital_records': [
            r'\b(birth certificate|death certificate|marriage license)\b',
            r'\b(vital record|certified copy)\b'
        ],
        'property': [
            r'\b(property|deed|title|assessment|parcel)\b',
            r'\b(real estate|land record)\b'
        ],
        'business': [
            r'\b(business|company|corporation|llc|dba)\b',
            r'\b(register|registration|ein|business license)\b'
        ],
        'health': [
            r'\b(health|medical|clinic|vaccination|immunization)\b',
            r'\b(food permit|restaurant|inspection)\b'
        ],
        'transportation': [
            r'\b(transit|bus|parking|vehicle|registration)\b',
            r'\b(traffic|transportation|metro)\b'
        ]
    }
    
    def __init__(self, use_bedrock: bool = True):
        """
        Initialize the classifier.
        
        Args:
            use_bedrock: Whether to attempt Bedrock classification (default: True)
        """
        self.use_bedrock = use_bedrock
        self.bedrock_client = None
        
        if use_bedrock:
            try:
                self.bedrock_client = boto3.client('bedrock-runtime')
            except Exception:
                # Bedrock not available, will use fallback
                self.bedrock_client = None
    
    def classify(self, problem_description: str, correlation_id: str) -> str:
        """
        Classifies problem into category.
        
        Args:
            problem_description: User's problem text
            correlation_id: Request tracing ID
        
        Returns:
            Category string (one of CATEGORIES)
        """
        # Try Bedrock classification first if enabled
        if self.use_bedrock and self.bedrock_client:
            try:
                category = self._classify_with_bedrock(problem_description, correlation_id)
                if category:
                    return category
            except Exception as e:
                # Log error and fall back to rule-based
                print(f"[{correlation_id}] Bedrock classification failed: {e}, using fallback")
        
        # Fallback to rule-based classification
        return self._classify_with_rules(problem_description)
    
    def _classify_with_bedrock(self, problem_description: str, correlation_id: str) -> Optional[str]:
        """
        Classify using Amazon Bedrock (Claude 3 Haiku).
        
        Args:
            problem_description: User's problem text
            correlation_id: Request tracing ID
        
        Returns:
            Category string or None if classification fails
        """
        if not self.bedrock_client:
            return None
        
        # Construct prompt for classification
        prompt = f"""Classify this civic problem into exactly one category from this list:
{', '.join(self.CATEGORIES)}

Problem: {problem_description}

Return only the category name, nothing else."""
        
        try:
            # Call Bedrock with Claude 3 Haiku
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body={
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 50,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3
                },
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            import json
            response_body = json.loads(response['body'].read())
            category = response_body.get('content', [{}])[0].get('text', '').strip().lower()
            
            # Validate category
            if category in self.CATEGORIES:
                print(f"[{correlation_id}] Bedrock classified as: {category}")
                return category
            else:
                print(f"[{correlation_id}] Bedrock returned invalid category: {category}")
                return None
                
        except ClientError as e:
            print(f"[{correlation_id}] Bedrock ClientError: {e}")
            return None
        except Exception as e:
            print(f"[{correlation_id}] Bedrock error: {e}")
            return None
    
    def _classify_with_rules(self, problem_description: str) -> str:
        """
        Classify using rule-based keyword matching.
        
        Args:
            problem_description: User's problem text
        
        Returns:
            Category string (defaults to 'general' if no match)
        """
        problem_lower = problem_description.lower()
        
        # Score each category based on keyword matches
        scores = {}
        for category, patterns in self.KEYWORD_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, problem_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[category] = score
        
        # Return category with highest score
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])[0]
            return best_category
        
        # Default to general if no matches
        return 'general'
