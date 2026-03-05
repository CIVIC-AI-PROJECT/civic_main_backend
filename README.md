# Kiro Backend Civic Assistant

A serverless AWS-based civic assistance system that helps users identify appropriate government offices for their needs and provides actionable guidance.
## What it Does

The Civic Assistant helps users quickly find the correct government office for their issue and guides them through the process.

Instead of searching across multiple government websites, users can simply describe their problem (e.g., correcting a birth certificate or renewing a license). The system then:

1. Identifies the relevant government department
2. Finds the nearest office
3. Explains why that office is recommended
4. Provides a checklist of required documents
5. Suggests what to say when speaking to officials

This system is designed to simplify access to government services, especially for citizens who may not know which department handles their request.

## Overview

The Kiro Backend is built entirely on AWS managed services:
- **API Gateway**: REST API endpoint
- **Lambda**: Python 3.11 serverless functions
- **DynamoDB**: Office directory, templates, and session logs
- **Bedrock**: AI-generated explanations and scripts
- **Location Service**: Geocoding and distance calculations
- **KMS**: Encryption at rest

## Architecture

The system uses a fully serverless AWS architecture.

User Request
   ↓
API Gateway
   ↓
AWS Lambda (Python Backend)
   ↓
DynamoDB (Office Directory & Templates)
   ↓
Amazon Location Service (Distance Calculation)
   ↓
Amazon Bedrock (AI-generated explanations)
   ↓
Response with recommended office + guidance

### Services Used

| Service | Purpose |
|------|------|
| API Gateway | Public API endpoint |
| AWS Lambda | Backend logic |
| DynamoDB | Stores office directory and templates |
| Amazon Location Service | Geocoding and distance calculation |
| Amazon Bedrock | AI explanations and conversation scripts |
| AWS KMS | Encryption for sensitive data |

## Features

- Problem classification and office matching
- Distance-based office ranking
- AI-generated recommendations and conversation scripts
- Privacy-first design with minimal PII storage
- Graceful degradation when AI services unavailable
- Comprehensive structured logging with correlation IDs

## Prerequisites

- Python 3.11 or higher
- AWS Account with appropriate permissions
- AWS CLI configured with credentials

## Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing tools)
pip install -r requirements-dev.txt
```

### 3. Verify Installation

```bash
# Check Python version
python --version  # Should show Python 3.11.x

# Run tests (once implemented)
pytest tests/
```

## Project Structure

```
kiro-backend/
├── src/                    # Source code
│   ├── __init__.py
│   ├── lambda_handler.py   # Main Lambda handler
│   ├── validators.py       # Request validation
│   ├── classifiers.py      # Problem classification
│   ├── rankers.py          # Office ranking
│   ├── clients.py          # AWS service clients
│   └── models.py           # Data models
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── properties/        # Property-based tests
│   ├── contract/          # Contract tests
│   └── integration/       # Integration tests
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── setup.py               # Package setup
└── README.md              # This file
```

## Testing

The project uses a comprehensive testing strategy:

### Unit Tests
```bash
pytest tests/unit/
```

### Property-Based Tests
```bash
pytest tests/properties/
```

### Contract Tests
```bash
pytest tests/contract/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Coverage Report
```bash
pytest --cov=src --cov-report=html tests/
```

## Development Workflow

1. Activate virtual environment
2. Make code changes
3. Run tests: `pytest tests/`
4. Check coverage: `pytest --cov=src tests/`
5. Commit changes

## Deployment

The application uses AWS SAM (Serverless Application Model) for infrastructure as code.

### Prerequisites for Deployment

- AWS CLI configured with credentials
- AWS SAM CLI installed ([installation guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
- Sufficient AWS permissions for Lambda, API Gateway, DynamoDB, KMS, and Location Service

### Deploy to AWS

```bash
# Build the application
sam build

# Deploy (first time - interactive)
sam deploy --guided

# Deploy (subsequent times)
sam deploy
```

During guided deployment, you'll be prompted for:
- Stack name (e.g., `kiro-backend`)
- AWS Region (e.g., `us-east-1`)
- Confirm changes before deploy
- Allow SAM CLI IAM role creation
- Save arguments to configuration file

### Seed Sample Data

After successful deployment, seed the DynamoDB tables with sample offices and templates:

**Option 1: Using the seed script**
```bash
# Seed with default region (us-east-1)
./scripts/seed.sh

# Seed with specific region
./scripts/seed.sh us-west-2
```

**Option 2: Using Python directly**
```bash
# Set environment variables
export AWS_REGION=us-east-1
export OFFICES_TABLE_NAME=OfficesTable
export TEMPLATES_TABLE_NAME=TemplatesTable

# Run seeding script
python scripts/seed_dynamodb.py
```

**Option 3: During setup**
```bash
# Seed automatically during setup
SEED=true bash setup.sh
```

The seed data includes:
- 10 offices in Delhi
- 10 offices in Chandigarh
- 9 category templates (permits, licenses, taxes, vital_records, property, business, health, transportation, general)

### Verify Deployment

```bash
# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name kiro-backend \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text

# Test the endpoint
curl -X POST <API_ENDPOINT> \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: test-123" \
  -d '{
    "problem": "I need to renew my driver license",
    "city": "Delhi"
  }'
```

### Update Deployment

```bash
# After making code changes
sam build
sam deploy
```

### Delete Stack

```bash
# Remove all AWS resources
sam delete
```

**Note:** Deleting the stack will remove all DynamoDB tables and their data. Make sure to backup any important data first.

## License

Proprietary - All rights reserved
