# Requirements Document

## Introduction

The Kiro Backend is a serverless civic-assistant system that helps users identify the appropriate government office for their civic needs and provides guidance on what to bring and what to say. The system accepts a user problem description along with location information (latitude/longitude or city name), then returns structured recommendations including the nearest relevant office, alternatives, required documents, conversation scripts, and privacy information.

The backend is built entirely on AWS services and prioritizes security, minimal PII storage, and production-ready reliability with structured logging and testing.

## Glossary

- **API_Gateway**: AWS API Gateway service that receives HTTP requests and routes them to Lambda functions
- **Lambda_Handler**: AWS Lambda function that processes civic assistance requests
- **Request_Validator**: Component that validates incoming JSON requests against the input schema
- **Response_Builder**: Component that constructs JSON responses conforming to the output schema
- **Problem_Classifier**: Component that categorizes user problems into predefined categories
- **Office_Ranker**: Component that ranks offices by distance and relevance
- **Bedrock_Client**: Component that interfaces with Amazon Bedrock for text generation
- **Location_Service**: Amazon Location Service used for geocoding and distance calculations
- **OfficesTable**: DynamoDB table storing government office directory information
- **TemplatesTable**: DynamoDB table storing checklist and script templates by category
- **Session_Log**: DynamoDB record containing session_id, problem_category, city, and timestamps
- **Correlation_ID**: Unique identifier passed through all system components for request tracing
- **PII**: Personally Identifiable Information such as names, addresses, medical details, or documents
- **KMS**: AWS Key Management Service for encryption key management
- **SAM**: AWS Serverless Application Model for infrastructure as code
- **Output_Schema**: JSON schema defining the structure of API responses
- **Input_Schema**: JSON schema defining the structure of API requests

## Requirements

### Requirement 1: Accept User Requests

**User Story:** As a user, I want to submit my civic problem with location information, so that I can receive personalized office recommendations.

#### Acceptance Criteria

1. THE Request_Validator SHALL accept JSON requests containing problem description, optional latitude, optional longitude, and city name
2. WHEN latitude and longitude are not provided, THE Request_Validator SHALL accept requests with only city name and problem description
3. THE Request_Validator SHALL validate all incoming requests against the Input_Schema
4. WHEN a request fails schema validation, THE Request_Validator SHALL return a descriptive error message identifying the validation failure
5. THE API_Gateway SHALL assign a unique Correlation_ID to each incoming request
6. THE Lambda_Handler SHALL log the Correlation_ID with all CloudWatch log entries for request tracing

### Requirement 2: Parse and Validate Input

**User Story:** As a developer, I want strict input validation, so that the system processes only well-formed requests.

#### Acceptance Criteria

1. THE Input_Schema SHALL define required fields for problem description and city
2. THE Input_Schema SHALL define optional fields for latitude and longitude as decimal numbers
3. THE Request_Validator SHALL reject requests missing required fields
4. WHEN latitude or longitude values are outside valid ranges, THE Request_Validator SHALL return a range validation error
5. THE Request_Validator SHALL parse valid JSON requests into structured data objects
6. FOR ALL valid request objects, serializing then parsing then serializing SHALL produce equivalent JSON (round-trip property)

### Requirement 3: Geocode City Names

**User Story:** As a user, I want to provide only my city name, so that I can get recommendations without sharing precise coordinates.

#### Acceptance Criteria

1. WHEN a request contains city name but no coordinates, THE Location_Service SHALL geocode the city name to obtain center coordinates
2. WHEN geocoding fails for a city name, THE Location_Service SHALL return an error indicating the city could not be found
3. THE Location_Service SHALL return latitude and longitude coordinates for successfully geocoded cities
4. WHEN a request contains both city and coordinates, THE Lambda_Handler SHALL use the provided coordinates without geocoding

### Requirement 4: Classify User Problems

**User Story:** As a system, I want to categorize user problems, so that I can match them to appropriate office types and templates.

#### Acceptance Criteria

1. THE Problem_Classifier SHALL categorize problem descriptions into predefined problem categories
2. WHERE Bedrock is available, THE Problem_Classifier SHALL use Bedrock for problem classification
3. WHERE Bedrock is unavailable, THE Problem_Classifier SHALL use rule-based classification as fallback
4. THE Problem_Classifier SHALL return exactly one category per problem description
5. WHEN a problem cannot be classified with confidence, THE Problem_Classifier SHALL return a default general category

### Requirement 5: Query Office Directory

**User Story:** As a system, I want to retrieve relevant offices from the directory, so that I can recommend appropriate locations to users.

#### Acceptance Criteria

1. THE OfficesTable SHALL store office records with office_id, office_type, name, address, latitude, longitude, city, category tags, and optional hours
2. THE Lambda_Handler SHALL query OfficesTable by city and category tags matching the classified problem
3. THE Lambda_Handler SHALL retrieve all offices in the specified city that match at least one category tag
4. WHEN no offices match the category tags, THE Lambda_Handler SHALL retrieve all offices in the specified city
5. WHEN no offices exist for the specified city, THE Lambda_Handler SHALL return an error indicating no offices found

### Requirement 6: Calculate Office Distances

**User Story:** As a user, I want to see the nearest relevant office, so that I can minimize travel time.

#### Acceptance Criteria

1. THE Location_Service SHALL calculate distances between user coordinates and each office location
2. THE Location_Service SHALL return distance values in kilometers
3. THE Office_Ranker SHALL rank offices by distance from nearest to farthest
4. THE Office_Ranker SHALL select the nearest office as the primary recommendation
5. THE Office_Ranker SHALL select the next three nearest offices as alternatives
6. WHEN fewer than four offices are available, THE Office_Ranker SHALL return all available offices

### Requirement 7: Generate Office Recommendations

**User Story:** As a user, I want to understand why an office was recommended, so that I can make informed decisions.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL generate explanation text describing why the recommended office is appropriate
2. THE Bedrock_Client SHALL include office proximity, relevant services, and category match in explanations
3. THE Bedrock_Client SHALL format explanations as bullet points
4. THE Bedrock_Client SHALL apply guardrails preventing invention of legal guarantees or specific outcomes
5. THE Bedrock_Client SHALL include "verify at counter" language in all explanations

### Requirement 8: Retrieve Checklist Templates

**User Story:** As a user, I want to know what documents and steps are required, so that I can prepare before visiting the office.

#### Acceptance Criteria

1. THE TemplatesTable SHALL store template records with category, required documents array, steps array, and script style options
2. THE Lambda_Handler SHALL query TemplatesTable using the classified problem category
3. THE Lambda_Handler SHALL retrieve the documents array and steps array for the matched category
4. WHEN no template exists for the category, THE Lambda_Handler SHALL return a default template with general guidance
5. THE Response_Builder SHALL include the documents array and steps array in the checklist section of the response

### Requirement 9: Generate Conversation Scripts

**User Story:** As a user, I want guidance on what to say at the office, so that I can communicate my needs effectively.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL generate conversation scripts based on the problem category and template script style
2. THE Bedrock_Client SHALL include opening statements and follow-up questions in scripts
3. THE Bedrock_Client SHALL adapt script language and tone based on template style options
4. THE Bedrock_Client SHALL apply guardrails preventing scripts from making legal claims or guarantees
5. THE Bedrock_Client SHALL include phrases prompting users to verify information with office staff

### Requirement 10: Format Structured Responses

**User Story:** As a client application, I want responses in a consistent JSON format, so that I can reliably parse and display information.

#### Acceptance Criteria

1. THE Output_Schema SHALL define the structure for recommended office, alternatives array, checklist object, conversation script object, and privacy information
2. THE Response_Builder SHALL construct responses conforming to the Output_Schema
3. THE Response_Builder SHALL include all required fields in every response
4. WHEN response construction completes, THE Lambda_Handler SHALL validate the response against the Output_Schema
5. FOR ALL valid response objects, serializing then parsing then serializing SHALL produce equivalent JSON (round-trip property)

### Requirement 11: Minimize PII Storage

**User Story:** As a privacy-conscious user, I want minimal personal information stored, so that my privacy is protected.

#### Acceptance Criteria

1. THE Lambda_Handler SHALL store only session_id, problem_category, city, and timestamps in Session_Log records
2. THE Lambda_Handler SHALL NOT store user problem descriptions containing potential PII
3. THE Lambda_Handler SHALL NOT store latitude or longitude coordinates
4. THE Lambda_Handler SHALL NOT store user medical details or document information
5. THE Response_Builder SHALL include a privacy block in responses listing what data is stored and what is not stored

### Requirement 12: Encrypt Data at Rest

**User Story:** As a security administrator, I want data encrypted at rest, so that stored information is protected from unauthorized access.

#### Acceptance Criteria

1. THE OfficesTable SHALL use KMS encryption for data at rest
2. THE TemplatesTable SHALL use KMS encryption for data at rest
3. THE Session_Log records SHALL use KMS encryption for data at rest
4. THE Lambda_Handler SHALL use AWS KMS managed keys for encryption operations
5. WHERE encryption fails, THE Lambda_Handler SHALL return an error and SHALL NOT store unencrypted data

### Requirement 13: Log with Structured Traces

**User Story:** As a system operator, I want structured logging with correlation IDs, so that I can trace requests through the system.

#### Acceptance Criteria

1. THE Lambda_Handler SHALL log all processing steps to CloudWatch with structured JSON format
2. THE Lambda_Handler SHALL include the Correlation_ID in every log entry
3. THE Lambda_Handler SHALL log request start time, end time, and processing duration
4. WHEN errors occur, THE Lambda_Handler SHALL log error details with stack traces and Correlation_ID
5. THE Lambda_Handler SHALL log the problem category and city for each request without logging PII

### Requirement 14: Provide Infrastructure as Code

**User Story:** As a DevOps engineer, I want infrastructure defined as code, so that I can deploy and manage the system reliably.

#### Acceptance Criteria

1. THE deployment configuration SHALL use AWS SAM or AWS CDK for infrastructure definition
2. THE deployment configuration SHALL define API_Gateway, Lambda functions, DynamoDB tables, and IAM roles
3. THE deployment configuration SHALL configure KMS encryption for all DynamoDB tables
4. THE deployment configuration SHALL configure CloudWatch log groups with retention policies
5. THE deployment configuration SHALL configure Bedrock and Location_Service permissions for Lambda execution role

### Requirement 15: Validate with Unit Tests

**User Story:** As a developer, I want comprehensive unit tests, so that I can verify component behavior and catch regressions.

#### Acceptance Criteria

1. THE test suite SHALL include unit tests for Request_Validator covering valid and invalid inputs
2. THE test suite SHALL include unit tests for Office_Ranker covering distance calculations and ranking logic
3. THE test suite SHALL include unit tests for Bedrock response parsing covering successful and malformed responses
4. THE test suite SHALL include unit tests for Problem_Classifier covering all supported categories
5. WHEN all unit tests execute, THE test suite SHALL report pass or fail status for each test

### Requirement 16: Validate with Contract Tests

**User Story:** As an API consumer, I want contract tests ensuring schema compliance, so that I can trust the API response format.

#### Acceptance Criteria

1. THE test suite SHALL include contract tests validating responses against the Output_Schema
2. THE test suite SHALL include contract tests validating request parsing against the Input_Schema
3. THE contract tests SHALL verify all required fields are present in responses
4. THE contract tests SHALL verify field types match schema definitions
5. WHEN contract tests fail, THE test suite SHALL report which schema constraints were violated

### Requirement 17: Handle Bedrock Service Errors

**User Story:** As a system, I want graceful handling of Bedrock failures, so that the service remains available during AI service disruptions.

#### Acceptance Criteria

1. WHEN Bedrock requests timeout, THE Bedrock_Client SHALL return a default explanation and script
2. WHEN Bedrock returns errors, THE Bedrock_Client SHALL log the error with Correlation_ID and return default content
3. WHEN Bedrock is unavailable, THE Lambda_Handler SHALL complete the request using template-based content
4. THE Lambda_Handler SHALL include a flag in responses indicating whether Bedrock-generated content was used
5. THE Lambda_Handler SHALL NOT fail requests solely due to Bedrock unavailability

### Requirement 18: Handle Location Service Errors

**User Story:** As a system, I want graceful handling of Location Service failures, so that geocoding issues do not block all requests.

#### Acceptance Criteria

1. WHEN Location_Service geocoding fails, THE Lambda_Handler SHALL return an error response with suggestions for valid city names
2. WHEN Location_Service distance calculations fail, THE Office_Ranker SHALL rank offices by category relevance without distance sorting
3. WHEN Location_Service is unavailable, THE Lambda_Handler SHALL log the service status and attempt request completion without distance data
4. THE Response_Builder SHALL indicate in responses when distance information is unavailable
5. WHEN coordinates are provided directly, THE Lambda_Handler SHALL proceed without requiring Location_Service geocoding

### Requirement 19: Provide Sample Data

**User Story:** As a developer, I want sample requests and responses, so that I can understand the API format and test integrations.

#### Acceptance Criteria

1. THE documentation SHALL include sample JSON requests demonstrating all input variations
2. THE documentation SHALL include sample JSON responses demonstrating successful responses
3. THE documentation SHALL include sample error responses demonstrating validation failures
4. THE sample requests SHALL include examples with coordinates and examples with city only
5. THE sample responses SHALL demonstrate responses for different problem categories
