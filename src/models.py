"""
Data models for internal objects in the Kiro Backend civic assistant system.

These models represent structured data passed between components. They use
Python dataclasses for clean, type-safe data structures that align with the
JSON schemas but represent internal Python objects.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Coordinates:
    """Represents geographic coordinates."""
    latitude: float
    longitude: float

    def __post_init__(self):
        """Validate coordinate ranges."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")


@dataclass
class ValidationResult:
    """Result of request validation."""
    is_valid: bool
    parsed_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_field: Optional[str] = None


@dataclass
class Office:
    """Represents a government office."""
    office_id: str
    office_type: str
    name: str
    address: str
    latitude: float
    longitude: float
    city: str
    category_tags: List[str]
    hours: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    distance_km: Optional[float] = None  # Populated after distance calculation
    explanation: Optional[str] = None  # Populated for recommended office


@dataclass
class RankedOffices:
    """Result of office ranking with primary and alternatives."""
    primary: Office
    alternatives: List[Office] = field(default_factory=list)


@dataclass
class Checklist:
    """Checklist with required documents and preparation steps."""
    documents: List[str]
    steps: List[str]


@dataclass
class ConversationScript:
    """Conversation script for office visit."""
    opening: str
    follow_ups: List[str]
