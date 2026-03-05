#!/bin/bash
# Standalone script to seed DynamoDB tables
# Usage: ./scripts/seed.sh [region]

set -e

REGION=${1:-us-east-1}

echo "=========================================="
echo "Seeding DynamoDB Tables"
echo "=========================================="
echo "Region: $REGION"
echo ""

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found."
    echo "Please install AWS CLI and configure credentials."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found."
    exit 1
fi

# Set environment variables
export AWS_REGION=$REGION

# Get table names from CloudFormation stack outputs (if available)
STACK_NAME="kiro-backend"
if aws cloudformation describe-stacks --stack-name $STACK_NAME &> /dev/null; then
    echo "Fetching table names from CloudFormation stack..."
    export OFFICES_TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='OfficesTableName'].OutputValue" \
        --output text \
        --region $REGION)
    export TEMPLATES_TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='TemplatesTableName'].OutputValue" \
        --output text \
        --region $REGION)
    echo "  Offices Table: $OFFICES_TABLE_NAME"
    echo "  Templates Table: $TEMPLATES_TABLE_NAME"
else
    echo "Using default table names (OfficesTable, TemplatesTable)"
    export OFFICES_TABLE_NAME="OfficesTable"
    export TEMPLATES_TABLE_NAME="TemplatesTable"
fi

echo ""

# Run the seeding script
python3 scripts/seed_dynamodb.py

echo ""
echo "Seeding complete!"
