"""
Unit tests for the ProblemClassifier component.

Tests cover:
- Classification for each supported category
- Rule-based classification accuracy
- Default "general" category fallback
- Bedrock fallback behavior (MVP: stub implementation)
"""

import pytest
from src.problem_classifier import ProblemClassifier


class TestProblemClassifier:
    """Unit tests for ProblemClassifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance with Bedrock disabled for testing."""
        return ProblemClassifier(use_bedrock=False)
    
    def test_classify_permits_building_permit(self, classifier):
        """Test classification of building permit requests."""
        problem = "I need a building permit for my deck renovation"
        category = classifier.classify(problem, "test-001")
        assert category == "permits"
    
    def test_classify_permits_construction(self, classifier):
        """Test classification of construction permit requests."""
        problem = "How do I get a construction permit for electrical work?"
        category = classifier.classify(problem, "test-002")
        assert category == "permits"
    
    def test_classify_licenses_driver_license(self, classifier):
        """Test classification of driver's license requests."""
        problem = "I need to renew my driver's license"
        category = classifier.classify(problem, "test-003")
        assert category == "licenses"
    
    def test_classify_licenses_dmv(self, classifier):
        """Test classification of DMV-related requests."""
        problem = "Where is the DMV office for getting an ID card?"
        category = classifier.classify(problem, "test-004")
        assert category == "licenses"
    
    def test_classify_taxes_property_tax(self, classifier):
        """Test classification of property tax requests."""
        problem = "I need to pay my property taxes"
        category = classifier.classify(problem, "test-005")
        assert category == "taxes"
    
    def test_classify_taxes_business_tax(self, classifier):
        """Test classification of business tax requests."""
        problem = "How do I file my business tax return?"
        category = classifier.classify(problem, "test-006")
        assert category == "taxes"
    
    def test_classify_vital_records_birth_certificate(self, classifier):
        """Test classification of birth certificate requests."""
        problem = "I need a copy of my birth certificate"
        category = classifier.classify(problem, "test-007")
        assert category == "vital_records"
    
    def test_classify_vital_records_marriage_license(self, classifier):
        """Test classification of marriage license requests."""
        problem = "How do I apply for a marriage license?"
        category = classifier.classify(problem, "test-008")
        assert category == "vital_records"
    
    def test_classify_property_deed(self, classifier):
        """Test classification of property deed requests."""
        problem = "I need to get a copy of my property deed"
        category = classifier.classify(problem, "test-009")
        assert category == "property"
    
    def test_classify_property_assessment(self, classifier):
        """Test classification of property assessment requests."""
        problem = "How do I check my property assessment?"
        category = classifier.classify(problem, "test-010")
        assert category == "property"
    
    def test_classify_business_registration(self, classifier):
        """Test classification of business registration requests."""
        problem = "I want to register a new business"
        category = classifier.classify(problem, "test-011")
        assert category == "business"
    
    def test_classify_business_dba(self, classifier):
        """Test classification of DBA requests."""
        problem = "How do I file a DBA for my company?"
        category = classifier.classify(problem, "test-012")
        assert category == "business"
    
    def test_classify_health_vaccination(self, classifier):
        """Test classification of health/vaccination requests."""
        problem = "Where can I get my vaccination records?"
        category = classifier.classify(problem, "test-013")
        assert category == "health"
    
    def test_classify_health_clinic(self, classifier):
        """Test classification of health clinic requests."""
        problem = "I need to find a public health clinic"
        category = classifier.classify(problem, "test-014")
        assert category == "health"
    
    def test_classify_transportation_vehicle_registration(self, classifier):
        """Test classification of vehicle registration requests."""
        problem = "How do I register my vehicle?"
        category = classifier.classify(problem, "test-015")
        assert category == "transportation"
    
    def test_classify_transportation_parking(self, classifier):
        """Test classification of parking permit requests."""
        problem = "I need a parking permit for my car"
        category = classifier.classify(problem, "test-016")
        assert category == "transportation"
    
    def test_classify_general_no_keywords(self, classifier):
        """Test default to 'general' when no keywords match."""
        problem = "I have a question about something"
        category = classifier.classify(problem, "test-017")
        assert category == "general"
    
    def test_classify_general_vague_request(self, classifier):
        """Test default to 'general' for vague requests."""
        problem = "Can you help me with a civic matter?"
        category = classifier.classify(problem, "test-018")
        assert category == "general"
    
    def test_classify_case_insensitive(self, classifier):
        """Test that classification is case-insensitive."""
        problem = "I NEED A BUILDING PERMIT FOR MY DECK"
        category = classifier.classify(problem, "test-019")
        assert category == "permits"
    
    def test_classify_multiple_keywords_same_category(self, classifier):
        """Test that multiple keywords in same category increase confidence."""
        problem = "I need a building permit for construction and renovation"
        category = classifier.classify(problem, "test-020")
        assert category == "permits"
    
    def test_classify_returns_valid_category(self, classifier):
        """Test that classify always returns a valid category."""
        problems = [
            "building permit",
            "driver license",
            "property tax",
            "birth certificate",
            "random text here",
            "xyz abc def"
        ]
        for problem in problems:
            category = classifier.classify(problem, "test-021")
            assert category in ProblemClassifier.CATEGORIES
    
    def test_bedrock_disabled_uses_rules(self):
        """Test that disabling Bedrock uses rule-based classification."""
        classifier = ProblemClassifier(use_bedrock=False)
        problem = "I need a building permit"
        category = classifier.classify(problem, "test-022")
        assert category == "permits"
    
    def test_bedrock_stub_falls_back_to_rules(self):
        """Test that Bedrock stub implementation falls back to rules (MVP)."""
        # Even with Bedrock enabled, the stub should fall back to rules
        classifier = ProblemClassifier(use_bedrock=True)
        problem = "I need a driver's license"
        category = classifier.classify(problem, "test-023")
        assert category == "licenses"
    
    def test_correlation_id_logged(self, classifier, caplog):
        """Test that correlation_id is included in logs."""
        import logging
        caplog.set_level(logging.INFO)
        
        correlation_id = "test-correlation-123"
        classifier.classify("building permit", correlation_id)
        
        # Check that correlation_id appears in log records
        log_records = [record for record in caplog.records]
        assert any(
            hasattr(record, 'correlation_id') and record.correlation_id == correlation_id
            for record in log_records
        )
    
    def test_all_categories_have_patterns(self):
        """Test that all non-general categories have keyword patterns."""
        classifier = ProblemClassifier(use_bedrock=False)
        categories_with_patterns = set(classifier.KEYWORD_PATTERNS.keys())
        
        # All categories except 'general' should have patterns
        expected_categories = set(classifier.CATEGORIES) - {'general'}
        assert categories_with_patterns == expected_categories
    
    def test_keyword_patterns_are_valid_regex(self):
        """Test that all keyword patterns are valid regex."""
        import re
        classifier = ProblemClassifier(use_bedrock=False)
        
        for category, patterns in classifier.KEYWORD_PATTERNS.items():
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error:
                    pytest.fail(f"Invalid regex pattern in {category}: {pattern}")
