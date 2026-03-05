"""
Unit tests for LocationService component.

Tests cover:
- Successful geocoding
- Failed geocoding (city not found)
- Successful distance calculation
- Failed distance calculation
- Service unavailable handling
"""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError, BotoCoreError
from src.location_service import LocationService, GeocodingError
from src.models import Coordinates


class TestLocationServiceGeocoding:
    """Test cases for geocode_city method."""
    
    def test_successful_geocoding(self):
        """Test successful city geocoding returns valid coordinates."""
        # Arrange
        mock_client = Mock()
        mock_response = {
            'Results': [
                {
                    'Place': {
                        'Geometry': {
                            'Point': [-122.3321, 47.6062]  # [lon, lat] format
                        }
                    }
                }
            ]
        }
        mock_client.search_place_index_for_text.return_value = mock_response
        service = LocationService(client=mock_client)
        
        # Act
        result = service.geocode_city("Seattle", "test-correlation-id")
        
        # Assert
        assert isinstance(result, Coordinates)
        assert result.latitude == 47.6062
        assert result.longitude == -122.3321
    
    def test_geocoding_city_not_found(self):
        """Test geocoding raises GeocodingError when city not found."""
        # Arrange
        mock_client = Mock()
        mock_response = {'Results': []}  # Empty results
        mock_client.search_place_index_for_text.return_value = mock_response
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(GeocodingError) as exc_info:
            service.geocode_city("NonexistentCity", "test-correlation-id")
        
        assert "not found" in str(exc_info.value).lower()
        assert "NonexistentCity" in str(exc_info.value)
    
    def test_geocoding_client_error(self):
        """Test geocoding raises LocationServiceError on AWS client error."""
        # Arrange
        mock_client = Mock()
        error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Index not found'}}
        client_error = ClientError(error_response, 'search_place_index_for_text')
        mock_client.search_place_index_for_text.side_effect = client_error
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(LocationServiceError) as exc_info:
            service.geocode_city("Seattle", "test-correlation-id")
        
        assert "unavailable" in str(exc_info.value).lower()
    
    def test_geocoding_botocore_error(self):
        """Test geocoding raises LocationServiceError on BotoCore error."""
        # Arrange
        mock_client = Mock()
        botocore_error = BotoCoreError()
        mock_client.search_place_index_for_text.side_effect = botocore_error
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(LocationServiceError):
            service.geocode_city("Seattle", "test-correlation-id")
    
    def test_geocoding_unexpected_error(self):
        """Test geocoding raises LocationServiceError on unexpected errors."""
        # Arrange
        mock_client = Mock()
        mock_client.search_place_index_for_text.side_effect = ValueError("Unexpected")
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(LocationServiceError) as exc_info:
            service.geocode_city("Seattle", "test-correlation-id")
        
        assert "failed" in str(exc_info.value).lower()
    
    def test_geocoding_logs_correlation_id(self):
        """Test geocoding logs include correlation_id."""
        # Arrange
        mock_client = Mock()
        mock_response = {
            'Results': [
                {
                    'Place': {
                        'Geometry': {
                            'Point': [-122.3321, 47.6062]
                        }
                    }
                }
            ]
        }
        mock_client.search_place_index_for_text.return_value = mock_response
        service = LocationService(client=mock_client)
        
        with patch('src.location_service.logger') as mock_logger:
            # Act
            service.geocode_city("Seattle", "test-correlation-123")
            
            # Assert - check that logger.info was called with correlation_id
            assert mock_logger.info.called
            call_args = mock_logger.info.call_args_list
            # Check that at least one call includes correlation_id in extra
            assert any(
                'extra' in str(call) and 'test-correlation-123' in str(call)
                for call in call_args
            )


class TestLocationServiceDistanceCalculation:
    """Test cases for calculate_distances method."""
    
    def test_successful_distance_calculation(self):
        """Test successful distance calculation returns list of distances in km."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [
            Coordinates(latitude=47.6205, longitude=-122.3493),
            Coordinates(latitude=47.6587, longitude=-122.3088)
        ]
        
        mock_response_1 = {'Summary': {'Distance': 2.5}}
        mock_response_2 = {'Summary': {'Distance': 6.8}}
        mock_client.calculate_route.side_effect = [mock_response_1, mock_response_2]
        service = LocationService(client=mock_client)
        
        # Act
        result = service.calculate_distances(origin, destinations, "test-correlation-id")
        
        # Assert
        assert len(result) == 2
        assert result[0] == 2.5
        assert result[1] == 6.8
        assert all(isinstance(d, (int, float)) for d in result)
        assert all(d >= 0 for d in result)
    
    def test_distance_calculation_single_destination(self):
        """Test distance calculation with single destination."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [Coordinates(latitude=47.6205, longitude=-122.3493)]
        
        mock_response = {'Summary': {'Distance': 2.5}}
        mock_client.calculate_route.return_value = mock_response
        service = LocationService(client=mock_client)
        
        # Act
        result = service.calculate_distances(origin, destinations, "test-correlation-id")
        
        # Assert
        assert len(result) == 1
        assert result[0] == 2.5
    
    def test_distance_calculation_empty_destinations(self):
        """Test distance calculation with empty destinations list."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = []
        service = LocationService(client=mock_client)
        
        # Act
        result = service.calculate_distances(origin, destinations, "test-correlation-id")
        
        # Assert
        assert result == []
    
    def test_distance_calculation_client_error(self):
        """Test distance calculation raises LocationServiceError on AWS client error."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [Coordinates(latitude=47.6205, longitude=-122.3493)]
        
        error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Calculator not found'}}
        client_error = ClientError(error_response, 'calculate_route')
        mock_client.calculate_route.side_effect = client_error
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(LocationServiceError) as exc_info:
            service.calculate_distances(origin, destinations, "test-correlation-id")
        
        assert "failed" in str(exc_info.value).lower()
    
    def test_distance_calculation_botocore_error(self):
        """Test distance calculation raises LocationServiceError on BotoCore error."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [Coordinates(latitude=47.6205, longitude=-122.3493)]
        
        botocore_error = BotoCoreError()
        mock_client.calculate_route.side_effect = botocore_error
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(LocationServiceError):
            service.calculate_distances(origin, destinations, "test-correlation-id")
    
    def test_distance_calculation_unexpected_error(self):
        """Test distance calculation raises LocationServiceError on unexpected errors."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [Coordinates(latitude=47.6205, longitude=-122.3493)]
        
        mock_client.calculate_route.side_effect = KeyError("Summary")
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(LocationServiceError) as exc_info:
            service.calculate_distances(origin, destinations, "test-correlation-id")
        
        assert "failed" in str(exc_info.value).lower()
    
    def test_distance_calculation_partial_failure(self):
        """Test distance calculation fails on first error (doesn't continue)."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [
            Coordinates(latitude=47.6205, longitude=-122.3493),
            Coordinates(latitude=47.6587, longitude=-122.3088)
        ]
        
        mock_response = {'Summary': {'Distance': 2.5}}
        error_response = {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}}
        client_error = ClientError(error_response, 'calculate_route')
        mock_client.calculate_route.side_effect = [mock_response, client_error]
        service = LocationService(client=mock_client)
        
        # Act & Assert
        with pytest.raises(LocationServiceError):
            service.calculate_distances(origin, destinations, "test-correlation-id")
    
    def test_distance_calculation_logs_correlation_id(self):
        """Test distance calculation logs include correlation_id."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [Coordinates(latitude=47.6205, longitude=-122.3493)]
        
        mock_response = {'Summary': {'Distance': 2.5}}
        mock_client.calculate_route.return_value = mock_response
        service = LocationService(client=mock_client)
        
        with patch('src.location_service.logger') as mock_logger:
            # Act
            service.calculate_distances(origin, destinations, "test-correlation-456")
            
            # Assert - check that logger.info was called with correlation_id
            assert mock_logger.info.called
            call_args = mock_logger.info.call_args_list
            # Check that at least one call includes correlation_id in extra
            assert any(
                'extra' in str(call) and 'test-correlation-456' in str(call)
                for call in call_args
            )
    
    def test_distance_calculation_uses_correct_api_parameters(self):
        """Test distance calculation uses correct API parameters."""
        # Arrange
        mock_client = Mock()
        origin = Coordinates(latitude=47.6062, longitude=-122.3321)
        destinations = [Coordinates(latitude=47.6205, longitude=-122.3493)]
        
        mock_response = {'Summary': {'Distance': 2.5}}
        mock_client.calculate_route.return_value = mock_response
        service = LocationService(client=mock_client)
        
        # Act
        service.calculate_distances(origin, destinations, "test-correlation-id")
        
        # Assert
        mock_client.calculate_route.assert_called_once()
        call_kwargs = mock_client.calculate_route.call_args[1]
        assert call_kwargs['CalculatorName'] == service.route_calculator_name
        assert call_kwargs['DeparturePosition'] == [-122.3321, 47.6062]  # [lon, lat]
        assert call_kwargs['DestinationPosition'] == [-122.3493, 47.6205]  # [lon, lat]
        assert call_kwargs['TravelMode'] == 'Car'
        assert call_kwargs['DistanceUnit'] == 'Kilometers'


class TestLocationServiceInitialization:
    """Test cases for LocationService initialization."""
    
    def test_default_initialization(self):
        """Test LocationService initializes with default parameters."""
        # Act
        mock_client = Mock()
        service = LocationService(client=mock_client)
        
        # Assert
        assert service.place_index_name == "CivicAssistantIndex"
        assert service.route_calculator_name == "CivicAssistantRouteCalculator"
        assert service.client is not None
    
    def test_custom_initialization(self):
        """Test LocationService initializes with custom parameters."""
        # Act
        mock_client = Mock()
        service = LocationService(
            place_index_name="CustomIndex",
            route_calculator_name="CustomCalculator",
            client=mock_client
        )
        
        # Assert
        assert service.place_index_name == "CustomIndex"
        assert service.route_calculator_name == "CustomCalculator"
