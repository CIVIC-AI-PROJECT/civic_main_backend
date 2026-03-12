"""
Main Lambda handler for the Kiro Backend civic assistant system.

This module orchestrates the entire request processing flow:
1. Validate request
2. Classify problem
3. Geocode city (if needed)
4. Query offices from DynamoDB
5. Calculate distances and rank offices
6. Generate AI content
7. Build and return response
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

from src.request_validator import RequestValidator
from src.problem_classifier import ProblemClassifier
from src.location_service import LocationService, GeocodingError
from src.office_ranker import OfficeRanker
from src.bedrock_client import BedrockClient
from src.response_builder import ResponseBuilder
from src.models import Office, Coordinates, Checklist


# Get table names from environment
OFFICES_TABLE_NAME = os.environ.get('OFFICES_TABLE_NAME', 'OfficesTable')
TEMPLATES_TABLE_NAME = os.environ.get('TEMPLATES_TABLE_NAME', 'TemplatesTable')
SESSION_LOG_TABLE_NAME = os.environ.get('SESSION_LOG_TABLE_NAME', 'SessionLog')

# Initialize components (reused across warm invocations)
validator = RequestValidator()
classifier = ProblemClassifier(use_bedrock=True)
location_service = LocationService()
ranker = OfficeRanker()
bedrock_client = BedrockClient(use_bedrock=True)
response_builder = ResponseBuilder()

# DynamoDB client
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function.
    
    Args:
        event: API Gateway event
        context: Lambda context
    
    Returns:
        API Gateway response with statusCode and body
    """
    start_time = time.time()
    
    # Extract or generate correlation ID
    headers = event.get('headers', {})
    correlation_id = (
        headers.get('x-correlation-id') or 
        headers.get('X-Correlation-Id') or 
        str(uuid.uuid4())
    )
    
    print(f"[{correlation_id}] Request started")
    
    try:
        # Step 1: Validate request
        validation_result = validator.validate(event)
        if not validation_result.is_valid:
            print(f"[{correlation_id}] Validation failed: {validation_result.error_message}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Correlation-Id',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                },
                'body': json.dumps(response_builder.build_error_response(
                    error_type='validation_error',
                    message=validation_result.error_message,
                    correlation_id=correlation_id,
                    details={'field': validation_result.error_field}
                ))
            }
        
        request_data = validation_result.parsed_data
        problem = request_data['problem']
        city = request_data["city"].strip().lower()
        
        # Step 2: Classify problem
        category = classifier.classify(problem, correlation_id)
        print(f"[{correlation_id}] Classified as: {category}")
        
        # Step 3: Get coordinates (geocode if not provided)
        if 'latitude' in request_data and 'longitude' in request_data:
            coordinates = Coordinates(
                latitude=request_data['latitude'],
                longitude=request_data['longitude']
            )
            print(f"[{correlation_id}] Using provided coordinates")
        else:
            try:
                coordinates = location_service.geocode_city(city, correlation_id)
            except GeocodingError as e:
                print(f"[{correlation_id}] Geocoding failed: {e}")
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Correlation-Id',
                        'Access-Control-Allow-Methods': 'POST,OPTIONS'
                    },
                    'body': json.dumps(response_builder.build_error_response(
                        error_type='not_found',
                        message=f"Could not find city: {city}. Please check the spelling or try a nearby city.",
                        correlation_id=correlation_id
                    ))
                }
        
        # Step 4: Query offices from DynamoDB (with auto-discovery if needed)
        offices = query_offices(city, category, coordinates, correlation_id)
        
        if not offices:
            print(f"[{correlation_id}] No offices found for {city}")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Correlation-Id',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                },
                'body': json.dumps(response_builder.build_error_response(
                    error_type='not_found',
                    message=f"No offices found in {city}. Please try a different city.",
                    correlation_id=correlation_id
                ))
            }
        
        print(f"[{correlation_id}] Found {len(offices)} offices")
        
        # Step 5: Calculate distances
        office_coordinates = [
            Coordinates(latitude=office.latitude, longitude=office.longitude)
            for office in offices
        ]
        distances = location_service.calculate_distances(
            origin=coordinates,
            destinations=office_coordinates,
            correlation_id=correlation_id
        )
        
        # Step 6: Rank offices
        ranked = ranker.rank(offices, category, distances)
        print(f"[{correlation_id}] Ranked offices, primary: {ranked.primary.name}")
        
        # Step 7: Get template from DynamoDB
        template = get_template(category, correlation_id)
        checklist = Checklist(
            documents=template.get('documents', ['Government-issued ID', 'Proof of address']),
            steps=template.get('steps', ['Bring all relevant documents', 'Arrive during business hours'])
        )
        
        # Step 8: Generate AI content
        bedrock_used = True
        try:
            explanation = bedrock_client.generate_explanation(
                ranked.primary, category, correlation_id
            )
            ranked.primary.explanation = explanation
            
            script = bedrock_client.generate_script(
                category,
                template.get('script_style', 'formal'),
                correlation_id
            )
        except Exception as e:
            print(f"[{correlation_id}] Bedrock generation failed: {e}")
            bedrock_used = False
            ranked.primary.explanation = f"This office handles {category} matters in your area."
            script = bedrock_client._default_script(category, 'formal')
        
        # Step 9: Build response
        processing_time_ms = (time.time() - start_time) * 1000
        response = response_builder.build_success_response(
            primary_office=ranked.primary,
            alternatives=ranked.alternatives,
            checklist=checklist,
            script=script,
            bedrock_used=bedrock_used,
            correlation_id=correlation_id,
            processing_time_ms=processing_time_ms
        )
        
        # Step 10: Log session (minimal PII)
        log_session(correlation_id, category, city, bedrock_used, processing_time_ms)
        
        print(f"[{correlation_id}] Request completed in {processing_time_ms:.2f}ms")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlation_id,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Correlation-Id',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        print(f"[{correlation_id}] Internal error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Correlation-Id',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps(response_builder.build_error_response(
                error_type='internal_error',
                message='An internal error occurred. Please try again later.',
                correlation_id=correlation_id
            ))
        }


def query_offices(city: str, category: str, coordinates: Coordinates, correlation_id: str) -> list:
    """
    Query offices from DynamoDB by city and category.
    If no offices found, auto-discover using Amazon Location Service and cache them.
    
    Args:
        city: City name (normalized to lowercase)
        category: Problem category
        coordinates: User coordinates for biasing search
        correlation_id: Request tracing ID
    
    Returns:
        List of Office objects
    """
    try:
        table = dynamodb.Table(OFFICES_TABLE_NAME)
        
        # Step 1: Query DynamoDB by city using GSI
        print(f"[{correlation_id}] Querying DynamoDB for city='{city}', category='{category}'")
        response = table.query(
            IndexName='city-index',
            KeyConditionExpression='city = :city',
            ExpressionAttributeValues={':city': city}
        )
        
        items = response.get('Items', [])
        print(f"[{correlation_id}] DDB offices found: {len(items)}")
        
        # Step 2: Filter by category if possible
        category_matches = [
            item for item in items
            if category in item.get('category_tags', [])
        ]
        
        # Use category matches if found, otherwise all offices in city
        filtered_items = category_matches if category_matches else items
        
        # Step 3: If no offices found, auto-discover using Location Service
        if not filtered_items:
            print(f"[{correlation_id}] No cached offices for {city}/{category}, starting auto-discovery...")
            
            # Define broad search queries for discovery
            search_queries = [
                f"{category} office",
                f"{category} department",
                "municipal office",
                "district office",
                "government office"
            ]
            
            discovered_count = 0
            seen_locations = set()
            
            for query in search_queries:
                if discovered_count >= 10:
                    break
                
                search_text = f"{query} in {city}"
                print(f"[{correlation_id}] Searching Location Service: '{search_text}'")
                
                try:
                    # Search using Amazon Location Service
                    search_params = {
                        'IndexName': os.environ.get('PLACE_INDEX_NAME', 'CivicAssistantPlaceIndex'),
                        'Text': search_text,
                        'MaxResults': 10
                    }
                    
                    # Bias search near provided coordinates if available
                    if coordinates:
                        search_params['BiasPosition'] = [coordinates.longitude, coordinates.latitude]
                    
                    location_client = boto3.client('location')
                    response = location_client.search_place_index_for_text(**search_params)
                    
                    results = response.get('Results', [])
                    
                    for result in results:
                        if discovered_count >= 10:
                            break
                        
                        place = result['Place']
                        geometry = place['Geometry']
                        point = geometry['Point']  # [longitude, latitude]
                        
                        # Create location key to avoid duplicates
                        location_key = f"{point[1]:.4f},{point[0]:.4f}"
                        if location_key in seen_locations:
                            continue
                        seen_locations.add(location_key)
                        
                        # Extract office information
                        office_name = place.get('Label', f"{query.title()} - {city.title()}")
                        address = place.get('Label', 'Address not available')
                        
                        # Create office item for DynamoDB
                        office_item = {
                            'office_id': str(uuid.uuid4()),
                            'name': str(office_name),
                            'address': str(address),
                            'latitude': float(point[1]),
                            'longitude': float(point[0]),
                            'city': city,  # Already normalized to lowercase
                            'office_type': 'government',
                            'category_tags': [category],
                            'created_at': datetime.utcnow().isoformat() + 'Z',
                            'updated_at': datetime.utcnow().isoformat() + 'Z'
                        }
                        
                        # Write to DynamoDB immediately
                        try:
                            table.put_item(Item=office_item)
                            discovered_count += 1
                            print(f"[{correlation_id}] Cached to DynamoDB: {office_name}")
                        except Exception as e:
                            print(f"[{correlation_id}] Error caching office: {e}")
                            continue
                    
                except Exception as e:
                    print(f"[{correlation_id}] Location Service search failed for '{search_text}': {e}")
                    continue
            
            print(f"[{correlation_id}] Location discovered: {discovered_count}")
            print(f"[{correlation_id}] Cached to Dynamo: {discovered_count}")
            
            # Step 4: Re-query DynamoDB after caching
            if discovered_count > 0:
                print(f"[{correlation_id}] Re-querying DynamoDB after discovery...")
                response = table.query(
                    IndexName='city-index',
                    KeyConditionExpression='city = :city',
                    ExpressionAttributeValues={':city': city}
                )
                items = response.get('Items', [])
                
                # Filter by category again
                category_matches = [
                    item for item in items
                    if category in item.get('category_tags', [])
                ]
                filtered_items = category_matches if category_matches else items
                print(f"[{correlation_id}] Re-query offices found: {len(filtered_items)}")
        
        # Step 5: Convert to Office objects
        offices = []
        for item in filtered_items:
            office = Office(
                office_id=item['office_id'],
                office_type=item.get('office_type', 'government'),
                name=item['name'],
                address=item['address'],
                latitude=float(item['latitude']),
                longitude=float(item['longitude']),
                city=item['city'],
                category_tags=item.get('category_tags', []),
                hours=item.get('hours'),
                phone=item.get('phone')
            )
            offices.append(office)
        
        return offices
        
    except ClientError as e:
        print(f"[{correlation_id}] DynamoDB query error: {e}")
        return []
    except Exception as e:
        print(f"[{correlation_id}] Office query error: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_template(category: str, correlation_id: str) -> dict:
    """
    Get template from DynamoDB by category.
    
    Args:
        category: Problem category
        correlation_id: Request tracing ID
    
    Returns:
        Template dict with documents, steps, script_style
    """
    try:
        table = dynamodb.Table(TEMPLATES_TABLE_NAME)
        
        response = table.get_item(Key={'category': category})
        
        if 'Item' in response:
            return response['Item']
        else:
            # Return default template
            print(f"[{correlation_id}] No template for {category}, using default")
            return {
                'category': 'general',
                'documents': ['Government-issued ID', 'Proof of address'],
                'steps': [
                    'Bring all relevant documents',
                    'Arrive during business hours',
                    'Be prepared to explain your situation'
                ],
                'script_style': 'formal'
            }
            
    except Exception as e:
        print(f"[{correlation_id}] Template query error: {e}")
        return {
            'category': 'general',
            'documents': ['Government-issued ID'],
            'steps': ['Bring relevant documents'],
            'script_style': 'formal'
        }


def log_session(
    correlation_id: str,
    category: str,
    city: str,
    bedrock_used: bool,
    processing_time_ms: float
):
    """
    Log session to DynamoDB (minimal PII).
    
    Args:
        correlation_id: Request correlation ID
        category: Problem category
        city: City name
        bedrock_used: Whether Bedrock was used
        processing_time_ms: Processing duration
    """
    try:
        table = dynamodb.Table(SESSION_LOG_TABLE_NAME)
        
        from datetime import datetime
        
        table.put_item(Item={
            'session_id': str(uuid.uuid4()),
            'correlation_id': correlation_id,
            'problem_category': category,
            'city': city,
            'timestamp': datetime.utcnow().isoformat(),
            'bedrock_used': bedrock_used,
            'processing_duration_ms': int(processing_time_ms)
        })
        
    except Exception as e:
        # Don't fail request if logging fails
        print(f"[{correlation_id}] Session logging failed: {e}")
