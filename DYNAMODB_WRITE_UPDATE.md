# DynamoDB Write Update for LocationService

## Changes Made

Updated `LocationService._save_offices_to_dynamodb()` to use individual `table.put_item()` calls instead of `batch_writer()`.

## Updated Method

### LocationService._save_offices_to_dynamodb()

```python
def _save_offices_to_dynamodb(self, offices: List[Office], correlation_id: str) -> None:
    """
    Save discovered offices to DynamoDB using put_item.
    
    Each office is written individually to ensure all required fields are stored:
    - office_id
    - name
    - address
    - latitude
    - longitude
    - city
    - office_type
    - category_tags
    
    Args:
        offices: List of Office objects to save
        correlation_id: Request tracing ID
    """
    if not offices:
        return
    
    try:
        table = self.dynamodb.Table(self.offices_table_name)
        saved_count = 0
        
        for office in offices:
            try:
                # Convert Office object to dict for DynamoDB
                # Include all required fields
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
                
                # Write to DynamoDB using put_item
                table.put_item(Item=item)
                saved_count += 1
                print(f"[{correlation_id}] Saved office: {office.office_id} - {office.name}")
                
            except ClientError as e:
                print(f"[{correlation_id}] Error saving office {office.office_id}: {e}")
                continue
            except Exception as e:
                print(f"[{correlation_id}] Unexpected error saving office {office.office_id}: {e}")
                continue
        
        print(f"[{correlation_id}] Successfully saved {saved_count}/{len(offices)} offices to DynamoDB")
        
    except Exception as e:
        print(f"[{correlation_id}] Error accessing DynamoDB table: {e}")
```

## Key Features

### 1. Individual put_item() Calls
- Each office is written separately using `table.put_item(Item=item)`
- Allows for individual error handling per office
- More granular logging for debugging

### 2. Required Fields Guaranteed
All discovered offices include these required fields:
- ✅ `office_id` - UUID generated during discovery
- ✅ `name` - Office name from Location Service
- ✅ `address` - Full address from Location Service
- ✅ `latitude` - Decimal degrees
- ✅ `longitude` - Decimal degrees
- ✅ `city` - City name from request
- ✅ `office_type` - Inferred from search query
- ✅ `category_tags` - Array with problem category

### 3. Optional Fields
- `hours` - Operating hours (if available)
- `phone` - Contact phone (if available)
- `created_at` - ISO 8601 timestamp
- `updated_at` - ISO 8601 timestamp

### 4. Error Handling
- Individual try-catch for each office write
- Continues processing remaining offices if one fails
- Logs specific errors with office_id
- Reports success count vs total count

### 5. Detailed Logging
```
[correlation-id] Saved office: uuid-123 - Office Name
[correlation-id] Saved office: uuid-456 - Another Office
[correlation-id] Successfully saved 10/10 offices to DynamoDB
```

## Flow Verification

### Complete Discovery Flow

```
1. User requests offices for city/category
   ↓
2. query_offices() queries DynamoDB
   ↓
3. No offices found → search_offices() called
   ↓
4. Location Service searches for offices
   ↓
5. Office objects created with all required fields
   ↓
6. _save_offices_to_dynamodb() called
   ↓
7. For each office:
   - Convert to DynamoDB item dict
   - Call table.put_item(Item=item)
   - Log success/failure
   ↓
8. Return discovered offices
   ↓
9. query_offices() re-queries DynamoDB
   ↓
10. Offices now found in cache
    ↓
11. Return to lambda_handler for ranking
```

## Example DynamoDB Item

```json
{
  "office_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "office_type": "municipal_corporation",
  "name": "Mumbai Municipal Corporation - Ward A",
  "address": "123 Main Road, Mumbai, Maharashtra 400001",
  "latitude": 18.9388,
  "longitude": 72.8354,
  "city": "Mumbai",
  "category_tags": ["vital_records"],
  "created_at": "2024-01-15T10:30:45.123Z",
  "updated_at": "2024-01-15T10:30:45.123Z"
}
```

## Benefits

### 1. Explicit Control
- Direct `put_item()` calls provide explicit control over each write
- Easier to debug individual write failures
- Clear logging for each operation

### 2. Error Resilience
- If one office write fails, others continue
- Partial success is possible and tracked
- No all-or-nothing batch behavior

### 3. Audit Trail
- Each office write is logged individually
- Easy to trace which offices were saved
- Clear success/failure reporting

### 4. Consistency
- All required fields are explicitly listed in code
- Easy to verify what data is being stored
- Clear documentation of data structure

## Testing

### Verification Commands

```bash
# 1. Import check
python -c "from src.location_service import LocationService; print('✓ Imports successful')"

# 2. Instantiation check
python -c "from src.location_service import LocationService; ls = LocationService(); print('✓ Instantiation successful')"

# 3. Full lambda handler check
python -c "from src.lambda_handler import lambda_handler; print('✓ Lambda handler imports successfully')"
```

### Expected CloudWatch Logs

When auto-discovery runs:
```
[abc-123] No offices in DynamoDB for Mumbai/vital_records, auto-discovering...
[abc-123] Auto-discovering offices for city=Mumbai, category=vital_records
[abc-123] Searching: municipal corporation office in Mumbai
[abc-123] Discovered: Mumbai Municipal Corporation - Ward A
[abc-123] Saved office: a1b2c3d4-... - Mumbai Municipal Corporation - Ward A
[abc-123] Saved office: b2c3d4e5-... - Mumbai Municipal Corporation - Ward B
...
[abc-123] Successfully saved 10/10 offices to DynamoDB
[abc-123] Discovered and cached 10 offices
```

## Deployment

The updated code is ready for deployment:

```bash
# Build
sam build

# Deploy
sam deploy

# Test with new city
curl -X POST <API_ENDPOINT> \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "I need a birth certificate",
    "city": "Mumbai"
  }'
```

## Summary

✅ Updated `_save_offices_to_dynamodb()` to use `table.put_item()`  
✅ All required fields explicitly included in each write  
✅ Individual error handling per office  
✅ Detailed logging with correlation_id  
✅ Code compiles and imports successfully  
✅ Ready for deployment
