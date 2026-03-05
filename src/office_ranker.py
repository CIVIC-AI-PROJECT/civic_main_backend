"""
Office ranking component for the Kiro Backend civic assistant system.

This module ranks offices by distance and relevance to provide ordered
recommendations with a primary office and alternatives.
"""

from typing import List, Optional
from src.models import Office, RankedOffices


class OfficeRanker:
    """
    Ranks offices by distance and relevance.
    
    Ranking algorithm:
    1. Calculate score: -distance + (category_match ? 10 : 0)
    2. Sort by score descending (higher score = better)
    3. Select top office as primary
    4. Select next 3 as alternatives
    
    Handles:
    - Offices with and without distance data
    - Category relevance boost
    - Fewer than 4 offices
    """
    
    def rank(
        self,
        offices: List[Office],
        category: str,
        distances: Optional[List[float]] = None
    ) -> RankedOffices:
        """
        Ranks offices by distance and relevance.
        
        Args:
            offices: List of office objects from DynamoDB
            category: Classified problem category
            distances: Optional list of distances in km (parallel to offices)
        
        Returns:
            RankedOffices with primary and alternatives
        
        Raises:
            ValueError: If offices list is empty
        """
        if not offices:
            raise ValueError("Cannot rank empty office list")
        
        # Attach distances to offices if provided
        if distances and len(distances) == len(offices):
            for office, distance in zip(offices, distances):
                office.distance_km = distance
        
        # Calculate scores for each office
        scored_offices = []
        for office in offices:
            # Base score from distance (negative so closer = higher score)
            distance_score = -office.distance_km if office.distance_km is not None else 0
            
            # Category relevance boost
            category_boost = 10 if category in office.category_tags else 0
            
            # Total score
            score = distance_score + category_boost
            
            scored_offices.append((score, office))
        
        # Sort by score descending (highest score first)
        scored_offices.sort(key=lambda x: x[0], reverse=True)
        
        # Extract sorted offices
        sorted_offices = [office for score, office in scored_offices]
        
        # Select primary (first) and alternatives (next 3)
        primary = sorted_offices[0]
        alternatives = sorted_offices[1:4] if len(sorted_offices) > 1 else []
        
        return RankedOffices(
            primary=primary,
            alternatives=alternatives
        )
