# Deployment Changes - Office Auto-Discovery Fix

## Summary

Fixed the civic assistant backend to ensure office auto-discovery works correctly and Delhi requests return proper results.

## Files Changed

### 1. src/lambda_handler.py ✅

**Changes:**
- Added `from datetime import datetime` import
- Normalized city name: `city = request_data["city"].strip().lower()`
- Updated `query_offices()` call to pass coordinates: `query_offices(city, category, coordinates, correlation_id)`
- Completely rewrote `query_offices()` function with:
  - City normalization (lowercase)
  - Clear CloudWatch logging at each step
  - Direct Amazon Location Service integration (removed dependency on LocationService.search_offices)
  - Broad search queries: `"{category} office"`, `"{category} department"`, `"municipal office"`, `"district office"`, `"government office"`
  - BiasPosition using provided coordinates
  - Individual `table.put_item()` for each discovered office
  - Proper float conversion for lat/lon
  - String conversion for name/address
  - Re-query after caching

**Key Logs Added:**
```python
print(f"[{correlation_id}] Querying DynamoDB for city='{city}', category='{category}'")
print(f"[{correlation_id}] DDB offices found: {len(items)}")
print(f"[{correlation_id}] Searching Location Service: '{search_text}'")
print(f"[{correlation_id}] Cached to DynamoDB: {office_name}")
print(f"[{correlation_id}] Location discovered: {discovered_count}")
print(f"[{correlation_id}] Cached to Dynamo: {discovered_count}")
print(f"[{correlation_id}] Re-query offices found: {len(filtered_items)}")
```

### 2. seed_data/offices.json ✅

**Changes:**
- Normalized all city names to lowercase
- Changed `"city": "Delhi"` → `"city": "delhi"`
- Changed `"city": "Chandigarh"` → `"city": "chandigarh"`

### 3. API_EXAMPLES.md ✅ (NEW FILE)

**Created comprehensive API documentation with:**
- Request/response formats
- Example requests for Delhi, Chandigarh, Mumbai, Bangalore
- cURL commands
- Postman collection setup
- Error response examples
- Auto-discovery feature explanation
- Test cases
- Rate limits and notes

## What Was Fixed

### Problem 1: Duplicate Discovery Logic ✅
**Before:** Auto-discovery logic existed in both `lambda_handler` and `query_offices()`, plus `LocationService.search_offices()`

**After:** Auto-discovery logic exists ONLY in `query_offices()`. Lambda handler just calls `query_offices()`.

### Problem 2: City Name Inconsistency ✅
**Before:** City names were mixed case ("Delhi", "Chandigarh") causing DynamoDB query mismatches

**After:** All city names normalized to lowercase everywhere:
- In lambda_handler: `city = city.strip().lower()`
- In DynamoDB writes: `'city': city` (already lowercase)
- In seed data: All cities lowercase

### Problem 3: Missing CloudWatch Logs ✅
**Before:** Limited logging made debugging difficult

**After:** Clear logs at every step:
- DDB offices found: X
- Location discovered: X
- Cached to Dynamo: X
- Re-query offices found: X

### Problem 4: DynamoDB Write Issues ✅
**Before:** Potential type mismatches

**After:** Explicit type conversions:
```python
'latitude': float(point[1]),
'longitude': float(point[0]),
'name': str(office_name),
'address': str(address),
'city': city  # Already lowercase string
```

### Problem 5: Narrow Search Queries ✅
**Before:** Category-specific queries might miss offices

**After:** Broad search queries:
- `"{category} office"`
- `"{category} department"`
- `"municipal office"`
- `"district office"`
- `"government office"`

### Problem 6: No Coordinate Biasing ✅
**Before:** Location searches didn't use user coordinates

**After:** BiasPosition parameter when coordinates available:
```python
if coordinates:
    search_params['BiasPosition'] = [coordinates.longitude, coordinates.latitude]
```

## Deployment Steps

### 1. Re-seed DynamoDB with Normalized Data

```bash
# Delete existing data (optional)
aws dynamodb scan --table-name OfficesTable \
  --attributes-to-get office_id \
  --query "Items[*].office_id.S" \
  --output text | \
  xargs -I {} aws dynamodb delete-item \
    --table-name OfficesTable \
    --key '{"office_id":{"S":"{}"}}'

# Seed with normalized data
python scripts/seed_dynamodb.py
```

### 2. Build and Deploy

```bash
# Build Lambda package
sam build

# Deploy to AWS
sam deploy

# Or if first time
sam deploy --guided
```

### 3. Get API Endpoint

```bash
aws cloudformation describe-stacks \
  --stack-name kiro-backend \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text
```

### 4. Test with Delhi Request

```bash
# Replace <API_ENDPOINT> with your actual endpoint
curl -X POST <API_ENDPOINT> \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: test-delhi-001" \
  -d '{
    "problem": "I need a birth certificate for my newborn child",
    "city": "Delhi"
  }'
```

**Expected Result:**
- First request: Auto-discovers offices (3-5 seconds)
- Returns 200 OK with office recommendations
- Subsequent requests: Uses cached data (< 1 second)

### 5. Verify CloudWatch Logs

```bash
# Get log group name
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/kiro-backend \
  --query "logGroups[0].logGroupName" \
  --output text

# Tail logs
aws logs tail /aws/lambda/kiro-backend-CivicAssistantFunction-XXX --follow
```

**Expected Logs (First Request):**
```
[test-delhi-001] Request started
[test-delhi-001] Classified as: vital_records
[test-delhi-001] Querying DynamoDB for city='delhi', category='vital_records'
[test-delhi-001] DDB offices found: 10
[test-delhi-001] Found 10 offices
[test-delhi-001] Ranked offices, primary: North Delhi Municipal Corporation Office
[test-delhi-001] Request completed in 1234.56ms
```

**Expected Logs (New City - Auto-Discovery):**
```
[test-mumbai-001] Request started
[test-mumbai-001] Classified as: vital_records
[test-mumbai-001] Querying DynamoDB for city='mumbai', category='vital_records'
[test-mumbai-001] DDB offices found: 0
[test-mumbai-001] No cached offices for mumbai/vital_records, starting auto-discovery...
[test-mumbai-001] Searching Location Service: 'vital_records office in mumbai'
[test-mumbai-001] Cached to DynamoDB: Mumbai Municipal Corporation - Ward A
[test-mumbai-001] Location discovered: 10
[test-mumbai-001] Cached to Dynamo: 10
[test-mumbai-001] Re-querying DynamoDB after discovery...
[test-mumbai-001] Re-query offices found: 10
[test-mumbai-001] Found 10 offices
[test-mumbai-001] Request completed in 4567.89ms
```

## Verification Checklist

- [ ] Code compiles: `python -c "from src.lambda_handler import lambda_handler; print('✓')"`
- [ ] SAM builds: `sam build`
- [ ] Deployed successfully: `sam deploy`
- [ ] API endpoint accessible: `curl <API_ENDPOINT>/civic-assist`
- [ ] Delhi request returns 200 OK
- [ ] CloudWatch logs show proper flow
- [ ] DynamoDB has normalized city names
- [ ] Auto-discovery works for new cities
- [ ] Subsequent requests use cache

## Rollback Plan

If issues occur:

```bash
# Rollback to previous version
aws cloudformation update-stack \
  --stack-name kiro-backend \
  --use-previous-template

# Or delete and redeploy
sam delete
sam deploy --guided
```

## Performance Expectations

- **Cached requests**: < 1 second
- **Auto-discovery (first request)**: 3-5 seconds
- **DynamoDB queries**: < 100ms
- **Location Service searches**: 1-2 seconds per query
- **Total with discovery**: ~4 seconds (5 search queries × 1s each)

## Cost Considerations

- **DynamoDB**: Pay per request (on-demand)
- **Lambda**: Pay per invocation and duration
- **Location Service**: Pay per search request
- **API Gateway**: Pay per request

**Optimization:**
- Offices cached after first discovery
- Subsequent requests only hit DynamoDB (cheaper)
- No repeated Location Service calls for same city

## Support

If Delhi request still returns "No offices found":

1. Check DynamoDB table has data:
```bash
aws dynamodb scan --table-name OfficesTable \
  --filter-expression "city = :city" \
  --expression-attribute-values '{":city":{"S":"delhi"}}' \
  --select COUNT
```

2. Check CloudWatch logs for errors:
```bash
aws logs tail /aws/lambda/kiro-backend-CivicAssistantFunction-XXX \
  --since 5m \
  --filter-pattern "ERROR"
```

3. Test DynamoDB query directly:
```bash
aws dynamodb query --table-name OfficesTable \
  --index-name city-index \
  --key-condition-expression "city = :city" \
  --expression-attribute-values '{":city":{"S":"delhi"}}'
```

4. Verify Location Service permissions:
```bash
aws iam get-role-policy \
  --role-name kiro-backend-CivicAssistantFunctionRole-XXX \
  --policy-name CivicAssistantFunctionRolePolicy
```
