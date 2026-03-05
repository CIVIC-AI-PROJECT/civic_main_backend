"""
Script to seed DynamoDB tables with sample data.

Usage:
    python seed_data/seed_dynamodb.py [--region us-west-2]
"""

import json
import argparse
import boto3
from datetime import datetime


def seed_offices(dynamodb, offices_data):
    """Seed OfficesTable with sample office data."""
    table = dynamodb.Table('OfficesTable')
    
    print("Seeding OfficesTable...")
    for office in offices_data:
        # Add timestamps
        office['created_at'] = datetime.utcnow().isoformat()
        office['updated_at'] = datetime.utcnow().isoformat()
        
        table.put_item(Item=office)
        print(f"  Added: {office['name']}")
    
    print(f"✓ Seeded {len(offices_data)} offices")


def seed_templates(dynamodb, templates_data):
    """Seed TemplatesTable with sample template data."""
    table = dynamodb.Table('TemplatesTable')
    
    print("\nSeeding TemplatesTable...")
    for template in templates_data:
        # Add timestamps
        template['created_at'] = datetime.utcnow().isoformat()
        template['updated_at'] = datetime.utcnow().isoformat()
        
        table.put_item(Item=template)
        print(f"  Added: {template['category']}")
    
    print(f"✓ Seeded {len(templates_data)} templates")


def main():
    parser = argparse.ArgumentParser(description='Seed DynamoDB tables with sample data')
    parser.add_argument('--region', default='us-west-2', help='AWS region (default: us-west-2)')
    parser.add_argument('--profile', help='AWS profile name (optional)')
    args = parser.parse_args()
    
    # Initialize DynamoDB client
    session_kwargs = {'region_name': args.region}
    if args.profile:
        session_kwargs['profile_name'] = args.profile
    
    session = boto3.Session(**session_kwargs)
    dynamodb = session.resource('dynamodb')
    
    # Load sample data
    with open('seed_data/sample_offices.json', 'r') as f:
        offices_data = json.load(f)
    
    with open('seed_data/sample_templates.json', 'r') as f:
        templates_data = json.load(f)
    
    # Seed tables
    try:
        seed_offices(dynamodb, offices_data)
        seed_templates(dynamodb, templates_data)
        
        print("\n✓ All data seeded successfully!")
        print("\nSummary:")
        print(f"  - {len(offices_data)} offices in OfficesTable")
        print(f"  - {len(templates_data)} templates in TemplatesTable")
        
    except Exception as e:
        print(f"\n✗ Error seeding data: {e}")
        raise


if __name__ == '__main__':
    main()
