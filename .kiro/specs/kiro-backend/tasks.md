# Implementation Plan: Kiro Backend Civic Assistant

## Overview

This implementation plan breaks down the serverless AWS civic assistant system into discrete, actionable tasks. The system is built with Python 3.11 on AWS Lambda, using API Gateway, DynamoDB, Bedrock, and Location Service. Each task builds incrementally toward a complete, production-ready system with comprehensive testing.

The implementation follows this sequence:
1. Project setup and infrastructure foundation
2. Core data models and schemas
3. Component implementations (validators, classifiers, rankers, clients)
4. Lambda handler integration
5. Infrastructure as code deployment
6. Comprehensive testing (unit, property-based, contract, integration)

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create Python 3.11 project with virtual environment
  - Install dependencies: boto3, jsonschema, hypothesis, pytest, pytest-cov
  - Create directory structure: src/, tests/unit/, tests/properties/, tests/contract/, tests/integration/
  - Set up .gitignore for Python projects
  - Create requirements.txt and requirements-dev.txt
  - _Requirements: 14.1, 15.1_

- [ ] 2. Define JSON schemas and data models
  - [x] 2.1 Create Input_Schema JSON schema definition
    - Define required fields: problem (10-1000 chars), city (2-100 chars)
    - Define optional fields: latitude (-90 to 90), longitude (-180 to 180)
    - Set additionalProperties to false
    - _Requirements: 1.1, 1.2, 2.1, 2.2_
  
  - [x] 2.2 Create Output_Schema JSON schema definition
    - Define recommended_office object with required fields
    - Define alternatives array structure
    - Define checklist object with documents and steps arrays
    - Define conversation_script object with opening and follow_ups
    - Define privacy object with stored and not_stored arrays
    - Define metadata object with correlation_id and bedrock_used
    - _Requirements: 10.1, 10.2_
  
  - [x] 2.3 Create Python data models for internal objects
    - Create ValidationResult, Office, Coordinates, RankedOffices, Checklist, ConversationScript classes
    - Add type hints for all fields
    - _Requirements: 2.5_

- [ ] 3. Implement Request_Validator component
  - [x] 3.1 Create RequestValidator class with validate method
    - Parse JSON body from API Gateway event
    - Validate against Input_Schema using jsonschema library
    - Check required fields (problem, city)
    - Validate coordinate ranges if provided
    - Return ValidationResult with parsed data or error details
    - Extract correlation_id from headers
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.3, 2.4, 2.5_
  
  - [x] 3.2 Write property test for valid request acceptance
    - **Property 1: Valid Request Acceptance**
    - **Validates: Requirements 1.1**
  
  - [x] 3.3 Write property test for invalid request rejection
    - **Property 2: Invalid Request Rejection with Descriptive Errors**
    - **Validates: Requirements 1.4, 2.3, 2.4**
  
  - [ ] 3.4 Write property test for request serialization round-trip
    - **Property 3: Request Serialization Round-Trip**
    - **Validates: Requirements 2.6**
  
  - [ ] 3.5 Write unit tests for RequestValidator
    - Test valid requests with all fields
    - Test valid requests with optional fields omitted
    - Test missing required fields
    - Test out-of-range coordinates
    - Test malformed JSON
    - Test wrong field types
    - _Requirements: 15.1_

- [ ] 4. Implement Problem_Classifier component
  - [x] 4.1 Create ProblemClassifier class with classify method
    - Define predefined categories: permits, licenses, taxes, vital_records, property, business, health, transportation, general
    - Implement Bedrock-based classification with Claude 3 Haiku
    - Implement rule-based fallback with keyword matching
    - Return exactly one category per request
    - Default to "general" when confidence is low
    - Log classification decisions with correlation_id
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 4.2 Write property test for classification returning valid category
    - **Property 7: Problem Classification Returns Valid Category**
    - **Validates: Requirements 4.1, 4.4**
  
  - [ ] 4.3 Write property test for classification fallback on Bedrock failure
    - **Property 8: Classification Fallback on Bedrock Failure**
    - **Validates: Requirements 4.3**
  
  - [ ] 4.4 Write unit tests for ProblemClassifier
    - Test classification for each supported category
    - Test Bedrock success path
    - Test Bedrock timeout fallback
    - Test Bedrock error fallback
    - Test rule-based classification
    - Test default "general" category
    - _Requirements: 15.4_

- [ ] 5. Implement Location_Service integration
  - [x] 5.1 Create LocationService class with geocode_city and calculate_distances methods
    - Implement geocode_city using Amazon Location Service SearchPlaceIndexForText
    - Return Coordinates with lat/lon
    - Raise GeocodingError when city not found
    - Implement calculate_distances using CalculateRoute API
    - Return distances in kilometers
    - Handle service unavailability gracefully
    - Log all calls with correlation_id
    - _Requirements: 3.1, 3.2, 3.3, 6.1, 6.2_
  
  - [ ] 5.2 Write property test for geocoding returning valid coordinates
    - **Property 5: City Geocoding Returns Coordinates**
    - **Validates: Requirements 3.1**
  
  - [ ] 5.3 Write property test for direct coordinates bypassing geocoding
    - **Property 6: Direct Coordinates Bypass Geocoding**
    - **Validates: Requirements 3.4**
  
  - [ ] 5.4 Write property test for distance calculation
    - **Property 12: Distance Calculation for All Offices**
    - **Validates: Requirements 6.1, 6.2**
  
  - [ ] 5.5 Write unit tests for LocationService
    - Test successful geocoding
    - Test failed geocoding (city not found)
    - Test successful distance calculation
    - Test failed distance calculation
    - Test service unavailable handling
    - _Requirements: 15.1_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement Office_Ranker component
  - [x] 7.1 Create OfficeRanker class with rank method
    - Sort offices by distance (nearest first)
    - Apply category relevance boost (matching category gets +10 score)
    - Calculate score: -distance + (category_match ? 10 : 0)
    - Select nearest office as primary recommendation
    - Select next 3 nearest as alternatives
    - Handle cases with fewer than 4 offices
    - Handle missing distance data (rank by relevance only)
    - _Requirements: 6.3, 6.4, 6.5, 6.6_
  
  - [ ] 7.2 Write property test for office ranking by distance
    - **Property 13: Office Ranking by Distance**
    - **Validates: Requirements 6.3**
  
  - [ ] 7.3 Write property test for alternative office selection
    - **Property 14: Alternative Office Selection**
    - **Validates: Requirements 6.5**
  
  - [ ] 7.4 Write property test for ranking without distances
    - **Property 34: Office Ranking Without Distances**
    - **Validates: Requirements 18.2**
  
  - [ ] 7.5 Write unit tests for OfficeRanker
    - Test ranking with 4+ offices
    - Test ranking with fewer than 4 offices
    - Test ranking with equal distances
    - Test ranking with missing distances
    - Test category relevance boost
    - _Requirements: 15.2_

- [ ] 8. Implement Bedrock_Client component
  - [ ] 8.1 Create BedrockClient class with generate_explanation and generate_script methods
    - Implement generate_explanation using Claude 3 Haiku
    - Format explanations as bullet points
    - Include office proximity, services, and category match
    - Apply guardrails preventing legal guarantees
    - Include "verify at counter" language
    - Implement generate_script with opening and follow-ups
    - Adapt tone based on template style (formal/casual)
    - Handle timeouts (5 seconds) and errors gracefully
    - Return default content on failure
    - Log all interactions with correlation_id
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ] 8.2 Write property test for explanation content requirements
    - **Property 15: Explanation Content Requirements**
    - **Validates: Requirements 7.2, 7.3, 7.5**
  
  - [ ] 8.3 Write property test for explanation generation
    - **Property 16: Explanation Generation**
    - **Validates: Requirements 7.1**
  
  - [ ] 8.4 Write property test for conversation script structure
    - **Property 20: Conversation Script Structure**
    - **Validates: Requirements 9.1, 9.2, 9.5**
  
  - [ ] 8.5 Write property test for Bedrock timeout fallback
    - **Property 30: Bedrock Timeout Fallback**
    - **Validates: Requirements 17.1**
  
  - [ ] 8.6 Write property test for Bedrock error fallback
    - **Property 31: Bedrock Error Fallback**
    - **Validates: Requirements 17.2**
  
  - [ ] 8.7 Write unit tests for BedrockClient
    - Test successful explanation generation
    - Test successful script generation
    - Test timeout handling
    - Test error response handling
    - Test default content fallback
    - Test guardrail verification (no legal guarantees)
    - _Requirements: 15.3_

- [ ] 9. Implement Response_Builder component
  - [-] 9.1 Create ResponseBuilder class with build_success_response and build_error_response methods
    - Construct response objects matching Output_Schema
    - Include all required fields
    - Add privacy information block with stored/not_stored arrays
    - Validate response against schema before returning
    - Format distances with units (km)
    - Include metadata (bedrock_used, correlation_id, processing_time_ms)
    - Build error responses with type, message, and details
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 11.5_
  
  - [ ] 9.2 Write property test for response schema conformance
    - **Property 21: Response Schema Conformance**
    - **Validates: Requirements 10.2**
  
  - [ ] 9.3 Write property test for response serialization round-trip
    - **Property 22: Response Serialization Round-Trip**
    - **Validates: Requirements 10.5**
  
  - [ ] 9.4 Write property test for privacy block in responses
    - **Property 24: Privacy Block in Responses**
    - **Validates: Requirements 11.5**
  
  - [ ] 9.5 Write property test for checklist inclusion
    - **Property 19: Checklist Inclusion in Response**
    - **Validates: Requirements 8.5**
  
  - [ ] 9.6 Write unit tests for ResponseBuilder
    - Test complete response with all fields
    - Test response with Bedrock content
    - Test response with default content
    - Test response with missing distances
    - Test privacy block inclusion
    - Test schema validation
    - _Requirements: 15.1_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Set up DynamoDB table definitions
  - [ ] 11.1 Create OfficesTable schema definition
    - Define partition key: office_id (string, UUID)
    - Define GSI: city-index with city as partition key
    - Define attributes: office_type, name, address, latitude, longitude, category_tags, hours, phone, created_at, updated_at
    - Configure KMS encryption at rest
    - _Requirements: 5.1, 12.1_
  
  - [ ] 11.2 Create TemplatesTable schema definition
    - Define partition key: category (string)
    - Define attributes: documents (array), steps (array), script_style, notes, created_at, updated_at
    - Configure KMS encryption at rest
    - Create default template for "general" category
    - _Requirements: 8.1, 12.2_
  
  - [ ] 11.3 Create Session_Log schema definition
    - Define partition key: session_id (string, UUID)
    - Define GSI: timestamp-index for time-based queries
    - Define attributes: correlation_id, problem_category, city, timestamp, bedrock_used, processing_duration_ms
    - Configure KMS encryption at rest
    - Ensure NO PII fields (no problem descriptions, coordinates, personal details)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 12.3_
  
  - [ ] 11.4 Write property test for session log PII constraints
    - **Property 23: Session Log PII Constraints**
    - **Validates: Requirements 11.1, 11.2, 11.3**

- [ ] 12. Implement Lambda_Handler main function
  - [ ] 12.1 Create lambda_handler function with event processing
    - Extract and assign Correlation_ID from headers or generate new UUID
    - Log request start with correlation_id
    - Call RequestValidator to validate input
    - Return 400 error for validation failures
    - Call ProblemClassifier to classify problem
    - Check if coordinates provided, otherwise call LocationService.geocode_city
    - Query OfficesTable by city and category
    - Fallback to all city offices if no category matches
    - Return 404 if no offices found
    - Call LocationService.calculate_distances
    - Call OfficeRanker to rank offices
    - Query TemplatesTable by category
    - Use default template if category not found
    - Call BedrockClient.generate_explanation
    - Call BedrockClient.generate_script
    - Call ResponseBuilder.build_success_response
    - Write Session_Log record with minimal PII
    - Log request completion with processing duration
    - Return 200 with response
    - Handle all errors with appropriate status codes and logging
    - _Requirements: 1.5, 1.6, 3.4, 4.1, 5.2, 5.3, 5.4, 5.5, 6.1, 7.1, 8.2, 8.3, 8.4, 10.4, 11.1, 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [ ] 12.2 Write property test for correlation ID in all logs
    - **Property 4: Correlation ID in All Logs**
    - **Validates: Requirements 1.6, 13.2**
  
  - [ ] 12.3 Write property test for office query using correct parameters
    - **Property 9: Office Query Uses Correct Parameters**
    - **Validates: Requirements 5.2**
  
  - [ ] 12.4 Write property test for office query returning category matches
    - **Property 10: Office Query Returns Category Matches**
    - **Validates: Requirements 5.3**
  
  - [ ] 12.5 Write property test for office query fallback
    - **Property 11: Office Query Fallback to All City Offices**
    - **Validates: Requirements 5.4**
  
  - [ ] 12.6 Write property test for template query by category
    - **Property 17: Template Query by Category**
    - **Validates: Requirements 8.2**
  
  - [ ] 12.7 Write property test for template retrieval returning required fields
    - **Property 18: Template Retrieval Returns Required Fields**
    - **Validates: Requirements 8.3**
  
  - [ ] 12.8 Write property test for request completion despite Bedrock failure
    - **Property 32: Request Completion Despite Bedrock Failure**
    - **Validates: Requirements 17.3**
  
  - [ ] 12.9 Write property test for Bedrock usage flag in response
    - **Property 33: Bedrock Usage Flag in Response**
    - **Validates: Requirements 17.4**
  
  - [ ] 12.10 Write property test for request completion without Location Service
    - **Property 35: Request Completion Without Location Service**
    - **Validates: Requirements 18.3**
  
  - [ ] 12.11 Write property test for distance unavailability indication
    - **Property 36: Distance Unavailability Indication**
    - **Validates: Requirements 18.4**
  
  - [ ] 12.12 Write property test for encryption failure preventing storage
    - **Property 25: Encryption Failure Prevents Storage**
    - **Validates: Requirements 12.5**
  
  - [ ] 12.13 Write property test for structured JSON logging
    - **Property 26: Structured JSON Logging**
    - **Validates: Requirements 13.1**
  
  - [ ] 12.14 Write property test for request timing in logs
    - **Property 27: Request Timing in Logs**
    - **Validates: Requirements 13.3**
  
  - [ ] 12.15 Write property test for error logging with stack traces
    - **Property 28: Error Logging with Stack Traces**
    - **Validates: Requirements 13.4**
  
  - [ ] 12.16 Write property test for category and city logging without PII
    - **Property 29: Category and City Logging Without PII**
    - **Validates: Requirements 13.5**

- [ ] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Create AWS SAM infrastructure as code
  - [ ] 14.1 Create SAM template.yaml
    - Define API Gateway REST API with POST /civic-assist endpoint
    - Configure HTTPS only, CORS, rate limiting (100 req/sec, burst 200)
    - Define Lambda function with Python 3.11 runtime
    - Configure Lambda timeout (30 seconds), memory (512 MB)
    - Define OfficesTable with city-index GSI
    - Define TemplatesTable
    - Define Session_Log with timestamp-index GSI
    - Configure KMS keys for each table
    - Enable automatic key rotation
    - _Requirements: 14.1, 14.2, 14.3_
  
  - [ ] 14.2 Create IAM execution role for Lambda
    - Grant DynamoDB Query/GetItem permissions for OfficesTable and TemplatesTable
    - Grant DynamoDB PutItem permission for Session_Log
    - Grant Bedrock InvokeModel permission for Claude 3 Haiku
    - Grant Location Service SearchPlaceIndexForText and CalculateRoute permissions
    - Grant KMS Decrypt/Encrypt/GenerateDataKey permissions for table keys
    - Grant CloudWatch Logs permissions
    - Apply principle of least privilege (no wildcards)
    - _Requirements: 14.2, 14.5_
  
  - [ ] 14.3 Configure CloudWatch log groups with retention
    - Create log group for Lambda function
    - Set retention policy (30 days for development, 90 days for production)
    - Enable structured JSON logging
    - _Requirements: 14.4_

- [ ] 15. Create sample data and seed scripts
  - [ ] 15.1 Create sample office data for testing
    - Create JSON file with sample offices for multiple cities
    - Include various office types and category tags
    - Include coordinates for distance testing
    - _Requirements: 19.1, 19.4_
  
  - [ ] 15.2 Create sample template data
    - Create JSON file with templates for all categories
    - Include documents, steps, and script styles
    - Include default "general" template
    - _Requirements: 19.5_
  
  - [ ] 15.3 Create DynamoDB seed script
    - Write Python script to load sample data into DynamoDB tables
    - Support both local DynamoDB and AWS deployment
    - _Requirements: 19.1_
  
  - [ ] 15.4 Create sample request/response documentation
    - Document sample requests with coordinates
    - Document sample requests with city only
    - Document sample successful responses for different categories
    - Document sample error responses (validation, not found, service errors)
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [ ] 16. Write contract tests for schema validation
  - [ ] 16.1 Write contract tests for Input_Schema
    - Test all valid request variations
    - Test all invalid request variations
    - Test field type mismatches
    - Test missing required fields
    - Test additional unexpected fields
    - _Requirements: 16.2_
  
  - [ ] 16.2 Write contract tests for Output_Schema
    - Test successful response structure
    - Test error response structure
    - Test all required fields present
    - Test correct field types
    - Test array length constraints
    - _Requirements: 16.1, 16.3, 16.4, 16.5_

- [ ] 17. Write integration tests
  - [ ] 17.1 Set up DynamoDB Local for integration testing
    - Configure DynamoDB Local in test environment
    - Seed test data for offices and templates
    - _Requirements: 15.1_
  
  - [ ] 17.2 Write integration test for full request flow
    - Test end-to-end request processing with mocked AWS services
    - Verify DynamoDB queries and writes
    - Verify response structure
    - _Requirements: 15.1_
  
  - [ ] 17.3 Write integration test for Bedrock fallback
    - Test request completion when Bedrock is mocked as unavailable
    - Verify default content is used
    - Verify bedrock_used flag is false
    - _Requirements: 17.3, 17.4_
  
  - [ ] 17.4 Write integration test for Location Service fallback
    - Test request completion when Location Service is mocked as unavailable
    - Verify ranking without distances
    - Verify distance fields indicate unavailability
    - _Requirements: 18.2, 18.3, 18.4_

- [ ] 18. Create deployment and testing documentation
  - [ ] 18.1 Create README.md with setup instructions
    - Document Python environment setup
    - Document dependency installation
    - Document AWS credentials configuration
    - Document local testing with DynamoDB Local
    - _Requirements: 14.1_
  
  - [ ] 18.2 Create deployment guide
    - Document SAM build and deploy commands
    - Document environment-specific configurations (dev, staging, prod)
    - Document rollback procedures
    - _Requirements: 14.1_
  
  - [ ] 18.3 Create testing guide
    - Document how to run unit tests
    - Document how to run property-based tests
    - Document how to run contract tests
    - Document how to run integration tests
    - Document coverage reporting
    - _Requirements: 15.5, 16.5_

- [ ] 19. Final checkpoint - Ensure all tests pass and deployment succeeds
  - Run full test suite (unit, property, contract, integration)
  - Verify test coverage meets 80% minimum
  - Deploy to development environment
  - Verify API Gateway endpoint is accessible
  - Test sample requests against deployed endpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- Contract tests ensure schema compliance
- Integration tests verify end-to-end flows with AWS services
- The implementation uses Python 3.11 as specified in the design document
- All AWS services (Bedrock, Location Service, DynamoDB) require proper IAM permissions
- KMS encryption is mandatory for all DynamoDB tables
- Structured JSON logging with correlation IDs enables full request tracing
- Graceful degradation ensures availability when AI services are unavailable
- PII minimization is enforced at all storage points
