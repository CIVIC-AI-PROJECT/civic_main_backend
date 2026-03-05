# Seed Data Documentation

This directory contains sample data for seeding DynamoDB tables.

## Files

### offices.json

Contains sample government office data for testing and development.

**Structure:**
```json
{
  "office_id": "unique-id",
  "office_type": "type of office",
  "name": "Official office name",
  "address": "Full street address",
  "latitude": 28.6289,
  "longitude": 77.2065,
  "city": "City name",
  "category_tags": ["category1", "category2"],
  "hours": "Operating hours",
  "phone": "Contact number"
}
```

**Current Data:**
- 10 offices in Delhi
- 10 offices in Chandigarh
- Total: 20 offices

**Office Types:**
- municipal_corporation
- rto (Regional Transport Office)
- tehsil_office / sub_registrar
- health_department
- business_registration
- tax_office
- building_permit
- police_station
- passport_office
- municipal_ward

**Categories:**
- permits
- licenses
- taxes
- vital_records
- property
- business
- health
- transportation
- general

### templates.json

Contains checklist and conversation script templates for each problem category.

**Structure:**
```json
{
  "category": "category_name",
  "documents": ["list", "of", "required", "documents"],
  "steps": ["preparation", "steps"],
  "script_style": "formal or casual"
}
```

**Current Data:**
- 9 category templates
- Covers all problem categories

## Adding More Data

### Adding Offices

1. Edit `offices.json`
2. Add new office object with all required fields
3. Ensure `office_id` is unique
4. Use accurate latitude/longitude coordinates
5. Assign appropriate `category_tags`

### Adding Templates

1. Edit `templates.json`
2. Add new template object for the category
3. Include comprehensive document list
4. Provide clear preparation steps
5. Choose appropriate `script_style` (formal/casual)

### Adding New Cities

To add offices for a new city:

1. Research actual government offices in that city
2. Get accurate addresses and coordinates
3. Add office entries to `offices.json` with the new city name
4. Ensure category coverage for common civic needs

## Seeding Process

The seeding script (`scripts/seed_dynamodb.py`) will:

1. Load JSON files from this directory
2. Add timestamps (`created_at`, `updated_at`) to each record
3. Insert/update items in DynamoDB tables
4. Report success/failure for each item

**Note:** The script uses `put_item`, which will overwrite existing items with the same key.

## Data Quality Guidelines

### Offices
- Use real addresses when possible
- Verify coordinates match addresses
- Include operating hours in local timezone
- Use international phone format (+91 for India)
- Assign multiple relevant category tags

### Templates
- Keep document lists comprehensive but practical
- Write steps in logical order
- Use clear, actionable language
- Consider user's perspective (what they need to know)
- Match script_style to office formality

## Testing Data

For testing purposes, you can create minimal test data:

```json
// Minimal office
{
  "office_id": "test-001",
  "office_type": "test",
  "name": "Test Office",
  "address": "Test Address",
  "latitude": 28.6,
  "longitude": 77.2,
  "city": "TestCity",
  "category_tags": ["general"]
}

// Minimal template
{
  "category": "test",
  "documents": ["ID"],
  "steps": ["Visit office"],
  "script_style": "casual"
}
```

## Production Considerations

Before deploying to production:

1. **Remove test data** - Use only real, verified office information
2. **Verify accuracy** - Double-check addresses, phone numbers, hours
3. **Update regularly** - Office information changes over time
4. **Add more cities** - Expand coverage based on user demand
5. **Localize content** - Consider multi-language support
6. **Legal review** - Ensure compliance with data accuracy requirements

## Backup and Recovery

To backup current DynamoDB data:

```bash
# Export offices
aws dynamodb scan --table-name OfficesTable > backup_offices.json

# Export templates
aws dynamodb scan --table-name TemplatesTable > backup_templates.json
```

To restore from backup, modify the JSON format to match seed data structure and re-run the seeding script.
