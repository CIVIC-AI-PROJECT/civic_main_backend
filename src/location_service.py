"""
Location service integration for the Kiro Backend civic assistant system.

This module provides geocoding and distance calculation using Amazon Location Service.
"""

import os
import uuid
from typing import List, Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from src.models import Coordinates, Office


class GeocodingError(Exception):
    """Raised when city geocoding fails."""
    pass


class LocationService:
    """
    Provides geocoding and distance calculation using Amazon Location Service.
    
    Features:
    - Geocode city names to lat/lon coordinates
    - Calculate distances between coordinates
    - Auto-discover offices when none exist for a city/category
    - Handle service unavailability gracefully
    """
    
    # Category to search query mapping for office discovery
    CATEGORY_SEARCH_QUERIES = {
        'permits': ['municipal corporation office', 'building permit office', 'town planning office'],
        'licenses': ['licensing office', 'municipal corporation office', 'RTO office'],
        'taxes': ['tax office', 'municipal corporation office', 'revenue office'],
        'vital_records': ['municipal corporation office', 'birth certificate office', 'SDM office'],
        'property': ['municipal corporation office', 'revenue office', 'tehsil office'],
        'business': ['business registration office', 'municipal corporation office', 'industries office'],
        'health': ['health department', 'municipal health office', 'civil hospital'],
        'transportation': ['RTO office', 'transport office', 'regional transport office'],
        'birth_certificate': ['municipal corporation office', 'birth certificate office', 'SDM office'],
        'income_certificate': ['SDM office', 'tehsil office', 'revenue office'],
        'police': ['police station', 'police headquarters'],
        'passport': ['passport seva kendra', 'passport office'],
        'ration_card': ['food supply office', 'ration office', 'civil supplies office'],
        'general': ['government office', 'municipal corporation office', 'district office']
    }
    
    def __init__(self, place_index_name: str = None):
        """
        Initialize the location service.
        
        Args:
            place_index_name: Name of the Amazon Location Service place index
        """
        self.place_index_name = place_index_name or os.environ.get('PLACE_INDEX_NAME', 'CivicAssistantPlaceIndex')
        self.offices_table_name = os.environ.get('OFFICES_TABLE_NAME', 'OfficesTable')
        
        try:
            self.location_client = boto3.client('location')
            self.dynamodb = boto3.resource('dynamodb')
        except Exception as e:
            print(f"Warning: Could not initialize AWS clients: {e}")
            self.location_client = None
            self.dynamodb = None
    
    def geocode_city(self, city_name: str, correlation_id: str) -> Coordinates:
        """
        Geocodes city name to coordinates using Amazon Location Service.
        
        Args:
            city_name: City name string
            correlation_id: Request tracing ID
        
        Returns:
            Coordinates with lat/lon
        
        Raises:
            GeocodingError: When city not found or service unavailable
        """
        if not self.location_client:
            raise GeocodingError("Location Service client not available")
        
        try:
            response = self.location_client.search_place_index_for_text(
                IndexName=self.place_index_name,
                Text=city_name,
                MaxResults=1
            )
            
            results = response.get('Results', [])
            if not results:
                raise GeocodingError(f"City not found: {city_name}")
            
            # Extract coordinates from first result
            place = results[0]['Place']
            geometry = place['Geometry']
            point = geometry['Point']  # [longitude, latitude]
            
            coordinates = Coordinates(
                latitude=point[1],
                longitude=point[0]
            )
            
            print(f"[{correlation_id}] Geocoded {city_name} to {coordinates.latitude}, {coordinates.longitude}")
            return coordinates
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            raise GeocodingError(f"Geocoding failed for {city_name}: {error_code}")
        except Exception as e:
            raise GeocodingError(f"Geocoding error for {city_name}: {str(e)}")
    
    def calculate_distances(
        self,
        origin: Coordinates,
        destinations: List[Coordinates],
        correlation_id: str
    ) -> List[float]:
        """
        Calculates distances from origin to destinations.
        
        Uses Haversine formula for distance calculation (great-circle distance).
        This is a fallback implementation that doesn't require Amazon Location Service
        routing API, which may have additional costs.
        
        Args:
            origin: User coordinates
            destinations: Office coordinates
            correlation_id: Request tracing ID
        
        Returns:
            List of distances in kilometers
        """
        import math
        
        distances = []
        
        for dest in destinations:
            # Haversine formula for great-circle distance
            lat1_rad = math.radians(origin.latitude)
            lat2_rad = math.radians(dest.latitude)
            delta_lat = math.radians(dest.latitude - origin.latitude)
            delta_lon = math.radians(dest.longitude - origin.longitude)
            
            a = (math.sin(delta_lat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            # Earth's radius in kilometers
            earth_radius_km = 6371.0
            distance_km = earth_radius_km * c
            
            distances.append(round(distance_km, 2))
        
        print(f"[{correlation_id}] Calculated {len(distances)} distances from origin")
        return distances
    
    def search_offices(
        self,
        city: str,
        category: str,
        correlation_id: str,
        max_results: int = 10
    ) -> List[Office]:
        """
        Search for offices using Amazon Location Service and cache them in DynamoDB.
        
        This method is called when no offices exist for a city/category combination.
        It searches for relevant offices using Location Service, creates Office objects,
        and saves them to DynamoDB for future queries.
        
        Args:
            city: City name to search in
            category: Problem category to determine search queries
            correlation_id: Request tracing ID
            max_results: Maximum number of offices to discover (default: 10)
        
        Returns:
            List of discovered Office objects
        """
        if not self.location_client or not self.dynamodb:
            print(f"[{correlation_id}] Location Service or DynamoDB not available for office discovery")
            return []
        
        print(f"[{correlation_id}] Auto-discovering offices for city={city}, category={category}")
        
        # Get search queries for this category
        search_queries = self.CATEGORY_SEARCH_QUERIES.get(
            category,
            self.CATEGORY_SEARCH_QUERIES['general']
        )
        
        discovered_offices = []
        seen_locations = set()  # Track unique locations to avoid duplicates
        
        # Search for each query type
        for query in search_queries:
            if len(discovered_offices) >= max_results:
                break
            
            search_text = f"{query} in {city}"
            print(f"[{correlation_id}] Searching: {search_text}")
            
            try:
                response = self.location_client.search_place_index_for_text(
                    IndexName=self.place_index_name,
                    Text=search_text,
                    MaxResults=5  # Get a few results per query
                )
                
                results = response.get('Results', [])
                
                for result in results:
                    if len(discovered_offices) >= max_results:
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
                    office_name = place.get('Label', f"{query.title()} - {city}")
                    address = place.get('Label', 'Address not available')
                    
                    # Create Office object
                    office = Office(
                        office_id=str(uuid.uuid4()),
                        office_type=self._infer_office_type(query),
                        name=office_name,
                        address=address,
                        latitude=point[1],
                        longitude=point[0],
                        city=city,
                        category_tags=[category],
                        hours=None,  # Not available from Location Service
                        phone=None,  # Not available from Location Service
                        created_at=datetime.utcnow().isoformat() + 'Z',
                        updated_at=datetime.utcnow().isoformat() + 'Z'
                    )
                    
                    discovered_offices.append(office)
                    print(f"[{correlation_id}] Discovered: {office_name}")
                
            except ClientError as e:
                print(f"[{correlation_id}] Search failed for '{search_text}': {e}")
                continue
            except Exception as e:
                print(f"[{correlation_id}] Error during search: {e}")
                continue
        
        # Save discovered offices to DynamoDB
        if discovered_offices:
            self._save_offices_to_dynamodb(discovered_offices, correlation_id)
        
        print(f"[{correlation_id}] Discovered and cached {len(discovered_offices)} offices")
        return discovered_offices
    
    def _infer_office_type(self, query: str) -> str:
        """
        Infer office type from search query.
        
        Args:
            query: Search query string
        
        Returns:
            Office type string
        """
        query_lower = query.lower()
        
        if 'municipal' in query_lower or 'corporation' in query_lower:
            return 'municipal_corporation'
        elif 'rto' in query_lower or 'transport' in query_lower:
            return 'rto'
        elif 'police' in query_lower:
            return 'police_station'
        elif 'passport' in query_lower:
            return 'passport_office'
        elif 'health' in query_lower or 'hospital' in query_lower:
            return 'health_department'
        elif 'tax' in query_lower or 'revenue' in query_lower:
            return 'tax_office'
        elif 'sdm' in query_lower or 'tehsil' in query_lower:
            return 'tehsil_office'
        elif 'business' in query_lower or 'industries' in query_lower:
            return 'business_registration'
        elif 'permit' in query_lower or 'building' in query_lower:
            return 'building_permit'
        elif 'food' in query_lower or 'ration' in query_lower:
            return 'food_supply'
        else:
            return 'government_office'
    
    def _save_offices_to_dynamodb(self, offices: List[Office], correlation_id: str) -> None:
        """
        Save discovered offices to DynamoDB using put_item.
        
        Each office is written individually to ensure all required fields are stored:
        - office_id
        - name
        - address
        - latitude
        - longitude
        - city
        - office_type
        - category_tags
        
        Args:
            offices: List of Office objects to save
            correlation_id: Request tracing ID
        """
        if not offices:
            return
        
        try:
            table = self.dynamodb.Table(self.offices_table_name)
            saved_count = 0
            
            for office in offices:
                try:
                    # Convert Office object to dict for DynamoDB
                    # Include all required fields
                    item = {
                        'office_id': office.office_id,
                        'office_type': office.office_type,
                        'name': office.name,
                        'address': office.address,
                        'latitude': office.latitude,
                        'longitude': office.longitude,
                        'city': office.city,
                        'category_tags': office.category_tags,
                        'created_at': office.created_at,
                        'updated_at': office.updated_at
                    }
                    
                    # Add optional fields if present
                    if office.hours:
                        item['hours'] = office.hours
                    if office.phone:
                        item['phone'] = office.phone
                    
                    # Write to DynamoDB using put_item
                    table.put_item(Item=item)
                    saved_count += 1
                    print(f"[{correlation_id}] Saved office: {office.office_id} - {office.name}")
                    
                except ClientError as e:
                    print(f"[{correlation_id}] Error saving office {office.office_id}: {e}")
                    continue
                except Exception as e:
                    print(f"[{correlation_id}] Unexpected error saving office {office.office_id}: {e}")
                    continue
            
            print(f"[{correlation_id}] Successfully saved {saved_count}/{len(offices)} offices to DynamoDB")
            
        except Exception as e:
            print(f"[{correlation_id}] Error accessing DynamoDB table: {e}")
