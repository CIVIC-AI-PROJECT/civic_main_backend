# Kiro Backend API Examples

## Base URL

```
https://<api-id>.execute-api.<region>.amazonaws.com/prod
```

Get your API endpoint after deployment:
```bash
aws cloudformation describe-stacks \
  --stack-name kiro-backend \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text
```

## Endpoint

```
POST /civic-assist
```

## Request Format

### Headers
```
Content-Type: application/json
X-Correlation-Id: <optional-uuid>
```

### Body Schema
```json
{
  "problem": "string (10-1000 chars, required)",
  "city": "string (2-100 chars, required)",
  "latitude": "number (optional, -90 to 90)",
  "longitude": "number (optional, -180 to 180)"
}
```

## Example Requests

### 1. Delhi - Birth Certificate (No Coordinates)

**Request:**
```json
POST /civic-assist
Content-Type: application/json

{
  "problem": "I need a birth certificate for my newborn child",
  "city": "Delhi"
}
```

**cURL:**
```bash
curl -X POST https://<api-endpoint>/civic-assist \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: test-delhi-001" \
  -d '{
    "problem": "I need a birth certificate for my newborn child",
    "city": "Delhi"
  }'
```

**Postman:**
```
Method: POST
URL: https://<api-endpoint>/civic-assist
Headers:
  Content-Type: application/json
  X-Correlation-Id: test-delhi-001
Body (raw JSON):
{
  "problem": "I need a birth certificate for my newborn child",
  "city": "Delhi"
}
```

### 2. Chandigarh - Driver License (With Coordinates)

**Request:**
```json
POST /civic-assist
Content-Type: application/json

{
  "problem": "I need to renew my driver's license",
  "city": "Chandigarh",
  "latitude": 30.7333,
  "longitude": 76.7794
}
```

**cURL:**
```bash
curl -X POST https://<api-endpoint>/civic-assist \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "I need to renew my driver'\''s license",
    "city": "Chandigarh",
    "latitude": 30.7333,
    "longitude": 76.7794
  }'
```

### 3. Mumbai - Property Tax

**Request:**
```json
POST /civic-assist
Content-Type: application/json

{
  "problem": "I need to pay my property tax",
  "city": "Mumbai"
}
```

**cURL:**
```bash
curl -X POST https://<api-endpoint>/civic-assist \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "I need to pay my property tax",
    "city": "Mumbai"
  }'
```

### 4. Bangalore - Business License

**Request:**
```json
POST /civic-assist
Content-Type: application/json

{
  "problem": "I need to register my new business and get a license",
  "city": "Bangalore"
}
```

## Response Format

### Success Response (200 OK)

```json
{
  "recommended_office": {
    "name": "North Delhi Municipal Corporation Office",
    "address": "Civic Centre, Minto Road, New Delhi, Delhi 110002",
    "distance_km": 2.3,
    "phone": "+91-11-23221111",
    "hours": "Mon-Fri 9:30am-5:30pm",
    "explanation": "• This office is closest to you (2.3 km away)\n• Handles birth certificate services\n• Please verify current requirements at the counter"
  },
  "alternatives": [
    {
      "name": "South Delhi Municipal Corporation",
      "address": "Nehru Place, New Delhi 110019",
      "distance_km": 5.7,
      "phone": "+91-11-26222000",
      "hours": "Mon-Fri 9:30am-5:30pm"
    }
  ],
  "checklist": {
    "documents": [
      "Government-issued photo ID (Aadhaar, Passport, or Voter ID)",
      "Proof of relationship (if requesting someone else's records)",
      "Hospital records or affidavit (for birth certificates)",
      "Application form duly filled"
    ],
    "steps": [
      "Determine which vital record you need",
      "Check if online application is available",
      "Bring original ID documents plus photocopies",
      "Have exact details (dates, names, registration numbers)",
      "Be patient as processing may take time"
    ]
  },
  "conversation_script": {
    "opening": "Hello, I need help with obtaining a birth certificate. Can you direct me to the right department?",
    "follow_ups": [
      "What documents do I need to bring?",
      "How long will the processing take?",
      "Is there an online application option?"
    ]
  },
  "privacy": {
    "stored": [
      "session_id",
      "problem_category",
      "city",
      "timestamp"
    ],
    "not_stored": [
      "problem_description",
      "coordinates",
      "personal_details"
    ]
  },
  "metadata": {
    "correlation_id": "test-delhi-001",
    "bedrock_used": true,
    "processing_time_ms": 1234
  }
}
```

### Error Responses

#### 400 Bad Request - Validation Error
```json
{
  "error": {
    "type": "validation_error",
    "message": "Missing required field: city",
    "details": {
      "field": "city",
      "correlation_id": "test-001"
    }
  }
}
```

#### 404 Not Found - City Not Found
```json
{
  "error": {
    "type": "not_found",
    "message": "Could not find city: InvalidCity. Please check the spelling or try a nearby city.",
    "details": {
      "correlation_id": "test-002"
    }
  }
}
```

#### 404 Not Found - No Offices
```json
{
  "error": {
    "type": "not_found",
    "message": "No offices found in SmallTown. Please try a different city.",
    "details": {
      "correlation_id": "test-003"
    }
  }
}
```

#### 500 Internal Server Error
```json
{
  "error": {
    "type": "internal_error",
    "message": "An internal error occurred. Please try again later.",
    "details": {
      "correlation_id": "test-004"
    }
  }
}
```

## Testing with Postman

### Import Collection

1. Open Postman
2. Click "Import"
3. Create new request with these settings:

**Request Name:** Kiro Backend - Delhi Birth Certificate

**Method:** POST

**URL:** `{{base_url}}/civic-assist`

**Headers:**
```
Content-Type: application/json
X-Correlation-Id: {{$guid}}
```

**Body (raw JSON):**
```json
{
  "problem": "I need a birth certificate for my newborn child",
  "city": "Delhi"
}
```

**Environment Variables:**
- `base_url`: Your API Gateway endpoint (without /civic-assist)

### Test Cases

#### Test 1: Valid Request - Delhi
```json
{
  "problem": "I need a birth certificate",
  "city": "Delhi"
}
```
Expected: 200 OK with office recommendations

#### Test 2: Valid Request - Chandigarh with Coordinates
```json
{
  "problem": "I need to renew my driver's license",
  "city": "Chandigarh",
  "latitude": 30.7333,
  "longitude": 76.7794
}
```
Expected: 200 OK with office recommendations

#### Test 3: Invalid - Missing City
```json
{
  "problem": "I need help with taxes"
}
```
Expected: 400 Bad Request

#### Test 4: Invalid - Problem Too Short
```json
{
  "problem": "Help",
  "city": "Delhi"
}
```
Expected: 400 Bad Request

#### Test 5: Invalid - Out of Range Coordinates
```json
{
  "problem": "I need a business license",
  "city": "Mumbai",
  "latitude": 200,
  "longitude": -122
}
```
Expected: 400 Bad Request

## Auto-Discovery Feature

The system automatically discovers offices for new cities using Amazon Location Service:

### First Request (Auto-Discovery)
```bash
curl -X POST https://<api-endpoint>/civic-assist \
  -H "Content-Type: application/json" \
  -d '{"problem": "I need a birth certificate", "city": "Mumbai"}'
```

**CloudWatch Logs:**
```
[correlation-id] Querying DynamoDB for city='mumbai', category='vital_records'
[correlation-id] DDB offices found: 0
[correlation-id] No cached offices for mumbai/vital_records, starting auto-discovery...
[correlation-id] Searching Location Service: 'vital_records office in mumbai'
[correlation-id] Cached to DynamoDB: Mumbai Municipal Corporation - Ward A
[correlation-id] Location discovered: 10
[correlation-id] Cached to Dynamo: 10
[correlation-id] Re-querying DynamoDB after discovery...
[correlation-id] Re-query offices found: 10
```

### Subsequent Requests (Cached)
```bash
curl -X POST https://<api-endpoint>/civic-assist \
  -H "Content-Type: application/json" \
  -d '{"problem": "I need a birth certificate", "city": "Mumbai"}'
```

**CloudWatch Logs:**
```
[correlation-id] Querying DynamoDB for city='mumbai', category='vital_records'
[correlation-id] DDB offices found: 10
```

## Rate Limits

- **Rate**: 100 requests/second per IP
- **Burst**: 200 requests

## Notes

1. **City Names**: Case-insensitive (automatically normalized to lowercase)
2. **Coordinates**: Optional but improve search accuracy when provided
3. **Correlation ID**: Optional but recommended for request tracing
4. **Auto-Discovery**: First request for a new city may take 3-5 seconds
5. **Caching**: Discovered offices are cached in DynamoDB for future requests
6. **Privacy**: Problem descriptions and coordinates are NOT stored

## Support

For issues or questions:
- Check CloudWatch logs with your correlation_id
- Verify API Gateway endpoint is correct
- Ensure AWS credentials have proper permissions
- Review DynamoDB tables for cached data
