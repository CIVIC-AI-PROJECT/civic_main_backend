"""
Quick MVP test script to verify core components work.

This script tests the main components without requiring AWS deployment.
"""

import json
from src.request_validator import RequestValidator
from src.problem_classifier import ProblemClassifier
from src.office_ranker import OfficeRanker
from src.response_builder import ResponseBuilder
from src.models import Office, Checklist, ConversationScript, Coordinates


def test_request_validator():
    """Test request validation."""
    print("Testing RequestValidator...")
    validator = RequestValidator()
    
    # Valid request
    event = {
        'body': json.dumps({
            'problem': 'I need to renew my driver license',
            'city': 'Seattle',
            'latitude': 47.6062,
            'longitude': -122.3321
        }),
        'headers': {'x-correlation-id': 'test-123'}
    }
    
    result = validator.validate(event)
    assert result.is_valid, f"Validation failed: {result.error_message}"
    assert result.parsed_data['problem'] == 'I need to renew my driver license'
    print("  ✓ Valid request accepted")
    
    # Invalid request (missing city)
    event_invalid = {
        'body': json.dumps({'problem': 'I need help'}),
        'headers': {}
    }
    
    result_invalid = validator.validate(event_invalid)
    assert not result_invalid.is_valid, "Invalid request was accepted"
    print("  ✓ Invalid request rejected")
    
    print("✓ RequestValidator tests passed\n")


def test_problem_classifier():
    """Test problem classification."""
    print("Testing ProblemClassifier...")
    classifier = ProblemClassifier(use_bedrock=False)  # Use rule-based only
    
    test_cases = [
        ("I need a building permit for my deck", "permits"),
        ("I need to renew my driver license", "licenses"),
        ("I need to pay my property taxes", "taxes"),
        ("I need a birth certificate", "vital_records"),
        ("I need help with something", "general")
    ]
    
    for problem, expected_category in test_cases:
        category = classifier.classify(problem, "test-correlation-id")
        assert category == expected_category, f"Expected {expected_category}, got {category}"
        print(f"  ✓ '{problem[:40]}...' → {category}")
    
    print("✓ ProblemClassifier tests passed\n")


def test_office_ranker():
    """Test office ranking."""
    print("Testing OfficeRanker...")
    ranker = OfficeRanker()
    
    # Create sample offices
    offices = [
        Office(
            office_id="1",
            office_type="city_hall",
            name="City Hall",
            address="123 Main St",
            latitude=47.6062,
            longitude=-122.3321,
            city="Seattle",
            category_tags=["permits", "licenses"]
        ),
        Office(
            office_id="2",
            office_type="dmv",
            name="DMV Office",
            address="456 Oak Ave",
            latitude=47.6189,
            longitude=-122.3208,
            city="Seattle",
            category_tags=["licenses", "transportation"]
        ),
        Office(
            office_id="3",
            office_type="tax_office",
            name="Tax Office",
            address="789 Pine St",
            latitude=47.6033,
            longitude=-122.3295,
            city="Seattle",
            category_tags=["taxes"]
        )
    ]
    
    distances = [2.5, 1.8, 3.2]
    
    ranked = ranker.rank(offices, "licenses", distances)
    
    assert ranked.primary.name == "DMV Office", "Wrong primary office selected"
    assert len(ranked.alternatives) == 2, "Wrong number of alternatives"
    print(f"  ✓ Primary: {ranked.primary.name} ({ranked.primary.distance_km} km)")
    print(f"  ✓ Alternatives: {len(ranked.alternatives)}")
    
    print("✓ OfficeRanker tests passed\n")


def test_response_builder():
    """Test response building."""
    print("Testing ResponseBuilder...")
    builder = ResponseBuilder()
    
    # Create sample data
    primary_office = Office(
        office_id="1",
        office_type="dmv",
        name="Seattle DMV",
        address="123 Main St, Seattle, WA",
        latitude=47.6062,
        longitude=-122.3321,
        city="Seattle",
        category_tags=["licenses"],
        distance_km=2.5,
        explanation="This DMV is closest to you and handles license renewals.",
        phone="(206) 555-0100",
        hours="Mon-Fri 9am-5pm"
    )
    
    alternatives = [
        Office(
            office_id="2",
            office_type="dmv",
            name="North Seattle DMV",
            address="456 Oak Ave, Seattle, WA",
            latitude=47.6189,
            longitude=-122.3208,
            city="Seattle",
            category_tags=["licenses"],
            distance_km=5.2
        )
    ]
    
    checklist = Checklist(
        documents=["Driver's license", "Proof of residency"],
        steps=["Bring documents", "Arrive early"]
    )
    
    script = ConversationScript(
        opening="Hello, I need to renew my driver's license.",
        follow_ups=["What documents do I need?", "How long will this take?"]
    )
    
    # Build response
    response = builder.build_success_response(
        primary_office=primary_office,
        alternatives=alternatives,
        checklist=checklist,
        script=script,
        bedrock_used=False,
        correlation_id="test-123",
        processing_time_ms=150.5
    )
    
    # Verify response structure
    assert "recommended_office" in response
    assert "alternatives" in response
    assert "checklist" in response
    assert "conversation_script" in response
    assert "privacy" in response
    assert "metadata" in response
    
    assert response["recommended_office"]["name"] == "Seattle DMV"
    assert response["recommended_office"]["distance_km"] == 2.5
    assert len(response["alternatives"]) == 1
    assert len(response["checklist"]["documents"]) == 2
    assert response["metadata"]["bedrock_used"] is False
    
    print("  ✓ Success response structure valid")
    
    # Test error response
    error_response = builder.build_error_response(
        error_type="validation_error",
        message="Missing required field",
        correlation_id="test-456"
    )
    
    assert "error" in error_response
    assert error_response["error"]["type"] == "validation_error"
    print("  ✓ Error response structure valid")
    
    print("✓ ResponseBuilder tests passed\n")


def main():
    """Run all MVP tests."""
    print("=" * 60)
    print("Kiro Backend MVP Component Tests")
    print("=" * 60 + "\n")
    
    try:
        test_request_validator()
        test_problem_classifier()
        test_office_ranker()
        test_response_builder()
        
        print("=" * 60)
        print("✓ All MVP component tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Deploy to AWS: sam build && sam deploy --guided")
        print("2. Seed data: python seed_data/seed_dynamodb.py")
        print("3. Test API endpoint with sample requests")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
