#!/usr/bin/env python3
"""
Seed script for DynamoDB tables.

This script reads JSON files from seed_data/ directory and populates
the OfficesTable and TemplatesTable in DynamoDB.

Usage:
    python scripts/seed_dynamodb.py [--region REGION]

Environment Variables:
    AWS_REGION: AWS region (default: us-east-1)
    OFFICES_TABLE_NAME: Name of offices table (default: OfficesTable)
    TEMPLATES_TABLE_NAME: Name of templates table (default: TemplatesTable)
"""
from decimal import Decimal
import json
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def load_json_file(file_path: str) -> list:
    """Load and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f, parse_float=Decimal)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def seed_offices_table(dynamodb, table_name: str, offices: list) -> None:
    """Seed the OfficesTable with office data."""
    table = dynamodb.Table(table_name)
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    print(f"\nSeeding {table_name}...")
    success_count = 0
    error_count = 0
    
    for office in offices:
        try:
            # Add timestamps if not present
            if 'created_at' not in office:
                office['created_at'] = timestamp
            if 'updated_at' not in office:
                office['updated_at'] = timestamp
            
            # Put item (will overwrite if exists)
            table.put_item(Item=office)
            print(f"  ✓ Inserted: {office['office_id']} - {office['name']}")
            success_count += 1
            
        except ClientError as e:
            print(f"  ✗ Error inserting {office.get('office_id', 'unknown')}: {e}")
            error_count += 1
    
    print(f"\nOffices: {success_count} succeeded, {error_count} failed")


def seed_templates_table(dynamodb, table_name: str, templates: list) -> None:
    """Seed the TemplatesTable with template data."""
    table = dynamodb.Table(table_name)
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    print(f"\nSeeding {table_name}...")
    success_count = 0
    error_count = 0
    
    for template in templates:
        try:
            # Add timestamps if not present
            if 'created_at' not in template:
                template['created_at'] = timestamp
            if 'updated_at' not in template:
                template['updated_at'] = timestamp
            
            # Put item (will overwrite if exists)
            table.put_item(Item=template)
            print(f"  ✓ Inserted: {template['category']}")
            success_count += 1
            
        except ClientError as e:
            print(f"  ✗ Error inserting {template.get('category', 'unknown')}: {e}")
            error_count += 1
    
    print(f"\nTemplates: {success_count} succeeded, {error_count} failed")


def verify_table_exists(dynamodb_client, table_name: str) -> bool:
    """Verify that a DynamoDB table exists."""
    try:
        dynamodb_client.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        raise


def main():
    """Main seeding function."""
    # Get configuration from environment or use defaults
    region = os.environ.get('AWS_REGION', 'us-east-1')
    offices_table = os.environ.get('OFFICES_TABLE_NAME', 'OfficesTable')
    templates_table = os.environ.get('TEMPLATES_TABLE_NAME', 'TemplatesTable')
    
    print("=" * 60)
    print("DynamoDB Seeding Script")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Offices Table: {offices_table}")
    print(f"Templates Table: {templates_table}")
    print("=" * 60)
    
    # Initialize boto3 clients
    try:
        dynamodb_client = boto3.client('dynamodb', region_name=region)
        dynamodb = boto3.resource('dynamodb', region_name=region)
    except Exception as e:
        print(f"Error: Failed to initialize AWS clients: {e}")
        print("Make sure AWS credentials are configured properly.")
        sys.exit(1)
    
    # Verify tables exist
    print("\nVerifying tables exist...")
    if not verify_table_exists(dynamodb_client, offices_table):
        print(f"Error: Table '{offices_table}' does not exist.")
        print("Please deploy the SAM template first: sam deploy")
        sys.exit(1)
    print(f"  ✓ {offices_table} exists")
    
    if not verify_table_exists(dynamodb_client, templates_table):
        print(f"Error: Table '{templates_table}' does not exist.")
        print("Please deploy the SAM template first: sam deploy")
        sys.exit(1)
    print(f"  ✓ {templates_table} exists")
    
    # Load seed data
    script_dir = Path(__file__).parent.parent
    offices_file = script_dir / 'seed_data' / 'offices.json'
    templates_file = script_dir / 'seed_data' / 'templates.json'
    
    print("\nLoading seed data...")
    offices = load_json_file(str(offices_file))
    print(f"  ✓ Loaded {len(offices)} offices from {offices_file.name}")
    
    templates = load_json_file(str(templates_file))
    print(f"  ✓ Loaded {len(templates)} templates from {templates_file.name}")
    
    # Seed tables
    seed_offices_table(dynamodb, offices_table, offices)
    seed_templates_table(dynamodb, templates_table, templates)
    
    print("\n" + "=" * 60)
    print("Seeding completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
