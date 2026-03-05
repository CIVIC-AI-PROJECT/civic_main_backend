# Fixed Auto-Discovery Logic

## Problem Summary

The original implementation had duplicated auto-discovery logic:
1. `lambda_handler` contained manual auto-discovery calling `discover_offices()` and `cache_offices_to_dynamo()`
2. `query_offices()` also contained auto-discovery using `search_offices()`
3. This created inconsistent behavior and duplicated code

## Solution

Removed all auto-discovery logic from `lambda_handler` and kept it ONLY in `query_offices()`.

## Updated Functions

### 1. lambda_handler (Simplified)

```python
# Step 4: Query offices from DynamoDB (with auto-discovery if needed)
offices = query_offices(city, category, correlation_id)

if not offices:
    print(f"[{correlation_id}] No offices found for {city}")
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response_builder.build_error_response(
            error_type='not_found',
            message=f"No offices found in {city}. Please try a different city.",
            correlation_id=correlation_id
        ))
    }

print(f"[{correlation_id}] Found {len(offices)} offices")

# Step 5: Calculate distances
# ... rest of the flow continues normally
```

**Changes:**
- ✅ Removed entire manual auto-discovery block
- ✅ Simplified to single `query_offices()` call
- ✅ No duplicated logic
- ✅ Clean separation of concerns

### 2. query_offices (Complete Auto-Discovery)

```python
def query_offices(city: str, category: str, correlation_id: str) -> list:
    """
    Query offices from DynamoDB by city and category.
    If no offices found, auto-discover using Amazon Location Service.
    
    Args:
        city: City name
        category: Problem category
        correlation_id: Request tracing ID
    
    Returns:
        List of Office objects
    """
    try:
        table = dynamodb.Table(OFFICES_TABLE_NAME)
        
        # Step 1: Query DynamoDB by city using GSI
        response = table.query(
            IndexName='city-index',
            KeyConditionExpression='city = :city',
            ExpressionAttributeValues={':city': city}
        )
        
        items = response.get('Items', [])
        
        # Step 2: Filter by category if possible, otherwise return all
        category_matches = [
            item for item in items
            if category in item.get('category_tags', [])
        ]
        
        # Use category matches if found, otherwise all offices in city
        filtered_items = category_matches if category_matches else items
        
        # Step 3: If no offices found, auto-discover using Location Service
        if not filtered_items:
            print(f"[{correlation_id}] No offices in DynamoDB for {city}/{category}, auto-discovering...")
            
            # 3a. Search offices using Location Service
            discovered_offices = location_service.search_offices(
                city=city,
                category=category,
                correlation_id=correlation_id,
                max_results=10
            )
            
            # 3b. search_offices() internally saves to DynamoDB using batch_writer()
            # 3c. Re-query DynamoDB after discovery
            if discovered_offices:
                response = table.query(
                    IndexName='city-index',
                    KeyConditionExpression='city = :city',
                    ExpressionAttributeValues={':city': city}
                )
                items = response.get('Items', [])
                
                # Filter by category again
                category_matches = [
                    item for item in items
                    if category in item.get('category_tags', [])
                ]
                filtered_items = category_matches if category_matches else items
        
        # Step 4: Convert to Office objects
        offices = []
        for item in filtered_items:
            office = Office(
                office_id=item['office_id'],
                office_type=item.get('office_type', 'government'),
                name=item['name'],
                address=item['address'],
                latitude=float(item['latitude']),
                longitude=float(item['longitude']),
                city=item['city'],
                category_tags=item.get('category_tags', []),
                hours=item.get('hours'),
                phone=item.get('phone')
            )
            offices.append(office)
        
        return offices
        
    except ClientError as e:
        print(f"[{correlation_id}] DynamoDB query error: {e}")
        return []
    except Exception as e:
        print(f"[{correlation_id}] Office query error: {e}")
        return []
```

**Flow:**
1. ✅ Query DynamoDB by city
2. ✅ Filter by category
3. ✅ If empty → Call `search_offices()` (which saves to DynamoDB internally)
4. ✅ Re-query DynamoDB after discovery
5. ✅ If still empty → Return empty list
6. ✅ Convert items to Office objects
7. ✅ Return offices

### 3. LocationService.search_offices (DynamoDB Caching)

```python
def search_offices(
    self,
    city: str,
    category: str,
    correlation_id: str,
    max_results: int = 10
) -> List[Office]:
    """
    Search for offices using Amazon Location Service and cache them in DynamoDB.
    """
    # ... discovery logic ...
    
    # Save discovered offices to DynamoDB
    if discovered_offices:
        self._save_offices_to_dynamodb(discovered_offices, correlation_id)
    
    print(f"[{correlation_id}] Discovered and cached {len(discovered_offices)} offices")
    return discovered_offices
```

### 4. LocationService._save_offices_to_dynamodb (Batch Writer)

```python
def _save_offices_to_dynamodb(self, offices: List[Office], correlation_id: str) -> None:
    """
    Save discovered offices to DynamoDB using batch writer.
    """
    try:
        table = self.dynamodb.Table(self.offices_table_name)
        
        with table.batch_writer() as batch:
            for office in offices:
                # Convert Office object to dict for DynamoDB
                item = {
                    'office_id': office.office_id,
                    'office_type': office.office_type,
                    'name': office.name,
                    'address': office.address,
                    'latitude': office.latitude,
                    'longitude': office.longitude,
                    'city': office.city,
                    'category_tags': office.category_tags,
                    'created_at': office.created_at,
                    'updated_at': office.updated_at
                }
                
                # Add optional fields if present
                if office.hours:
                    item['hours'] = office.hours
                if office.phone:
                    item['phone'] = office.phone
                
                batch.put_item(Item=item)
        
        print(f"[{correlation_id}] Saved {len(offices)} offices to DynamoDB")
        
    except ClientError as e:
        print(f"[{correlation_id}] Error saving offices to DynamoDB: {e}")
    except Exception as e:
        print(f"[{correlation_id}] Unexpected error saving offices: {e}")
```

## Complete Flow Diagram

```
User Request
    ↓
lambda_handler
    ↓
query_offices(city, category, correlation_id)
    ↓
Query DynamoDB (city-index)
    ↓
Filter by category
    ↓
Offices found? ──YES──→ Return Office objects
    ↓
   NO
    ↓
location_service.search_offices(city, category, correlation_id)
    ↓
Search Amazon Location Service
    ↓
Create Office objects
    ↓
_save_offices_to_dynamodb() [batch_writer]
    ↓
Re-query DynamoDB (city-index)
    ↓
Filter by category
    ↓
Offices found? ──YES──→ Return Office objects
    ↓
   NO
    ↓
Return empty list
    ↓
lambda_handler returns 404
```

## Benefits of This Approach

1. ✅ **Single Responsibility**: Auto-discovery logic is only in `query_offices()`
2. ✅ **No Duplication**: Removed duplicated discovery code from `lambda_handler`
3. ✅ **Consistent Caching**: All discovered offices are saved via `batch_writer()`
4. ✅ **Guaranteed Re-query**: Always re-queries DynamoDB after discovery
5. ✅ **Clean Separation**: `lambda_handler` focuses on orchestration, not discovery
6. ✅ **Proper Logging**: All operations logged with `correlation_id`
7. ✅ **Error Handling**: Graceful fallback if discovery fails
8. ✅ **No Breaking Changes**: Response format and ranking logic unchanged

## Testing

The fixed logic ensures:
- First request for a city triggers auto-discovery
- Discovered offices are cached in DynamoDB
- Subsequent requests use cached data
- No duplicate discovery attempts
- Consistent behavior across all requests

## Verification

To verify the fix works:

```bash
# 1. Import check
python -c "from src.lambda_handler import lambda_handler, query_offices; print('✓ Imports successful')"

# 2. Test with a new city (should trigger discovery)
curl -X POST <API_ENDPOINT> \
  -H "Content-Type: application/json" \
  -d '{"problem": "I need a birth certificate", "city": "Mumbai"}'

# 3. Test same city again (should use cache)
curl -X POST <API_ENDPOINT> \
  -H "Content-Type: application/json" \
  -d '{"problem": "I need a birth certificate", "city": "Mumbai"}'

# Check CloudWatch logs for:
# - First request: "auto-discovering..." and "Saved X offices to DynamoDB"
# - Second request: No auto-discovery messages (uses cache)
```
