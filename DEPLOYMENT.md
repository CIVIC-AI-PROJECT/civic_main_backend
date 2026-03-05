# Deployment Guide - Kiro Backend Civic Assistant

This guide walks through deploying the Kiro Backend MVP to AWS.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **AWS SAM CLI** installed ([Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
4. **Python 3.11** installed
5. **Bedrock Access** - Request access to Claude 3 Haiku in your AWS region
6. **Amazon Location Service** - Create a place index named "CivicAssistantIndex"

## Step 1: Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region
```

## Step 2: Set Up Amazon Location Service

```bash
# Create a place index for geocoding
aws location create-place-index \
    --index-name CivicAssistantIndex \
    --data-source Esri \
    --pricing-plan RequestBasedUsage
```

## Step 3: Request Bedrock Model Access

1. Go to AWS Console → Bedrock → Model access
2. Request access to "Claude 3 Haiku" model
3. Wait for approval (usually instant)

## Step 4: Build and Deploy with SAM

```bash
# Build the application
sam build

# Deploy (first time - guided)
sam deploy --guided

# Follow the prompts:
# - Stack Name: kiro-backend-prod
# - AWS Region: us-west-2 (or your preferred region)
# - Confirm changes before deploy: Y
# - Allow SAM CLI IAM role creation: Y
# - Save arguments to configuration file: Y

# Subsequent deployments (after first guided deploy)
sam deploy
```

## Step 5: Seed Sample Data

After deployment, seed the DynamoDB tables with sample data:

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install boto3 if not already installed
pip install boto3

# Seed the tables
python seed_data/seed_dynamodb.py --region us-west-2
```

## Step 6: Test the API

Get your API endpoint from the SAM deployment output or CloudFormation:

```bash
# Get the API endpoint
aws cloudformation describe-stacks \
    --stack-name kiro-backend-prod \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text
```

Test with curl:

```bash
# Example request
curl -X POST https://YOUR-API-ID.execute-api.us-west-2.amazonaws.com/prod/civic-assist \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: test-123" \
  -d '{
    "problem": "I need to renew my driver license",
    "city": "Seattle"
  }'
```

## Step 7: Monitor and Debug

### View Logs

```bash
# Tail Lambda logs
sam logs --tail --stack-name kiro-backend-prod

# View specific log group
aws logs tail /aws/lambda/kiro-backend-prod-CivicAssistantFunction --follow
```

### Check DynamoDB Tables

```bash
# List offices
aws dynamodb scan --table-name OfficesTable --max-items 5

# List templates
aws dynamodb scan --table-name TemplatesTable

# View session logs
aws dynamodb scan --table-name SessionLog --max-items 10
```

## Troubleshooting

### Issue: Bedrock Access Denied

**Solution:** Ensure you've requested and received access to Claude 3 Haiku in the Bedrock console.

### Issue: Location Service Not Found

**Solution:** Verify the place index "CivicAssistantIndex" exists:
```bash
aws location describe-place-index --index-name CivicAssistantIndex
```

### Issue: DynamoDB Table Not Found

**Solution:** Verify tables were created:
```bash
aws dynamodb list-tables
```

### Issue: Lambda Timeout

**Solution:** Check CloudWatch logs for specific errors. The timeout is set to 30 seconds in template.yaml.

## Cleanup

To remove all resources:

```bash
# Delete the CloudFormation stack
sam delete --stack-name kiro-backend-prod

# Delete the Location Service place index
aws location delete-place-index --index-name CivicAssistantIndex
```

## Cost Estimates

**Expected monthly costs for low-moderate usage:**

- API Gateway: ~$3.50 per million requests
- Lambda: ~$0.20 per million requests (512MB, 2s avg)
- DynamoDB: ~$1.25 per million reads (on-demand)
- Bedrock (Claude 3 Haiku): ~$0.25 per million input tokens
- Location Service: ~$4.00 per 1000 geocoding requests
- KMS: ~$1.00 per key per month

**Total for 10,000 requests/month: ~$5-10**

## Production Considerations

Before going to production:

1. **Enable API Gateway authentication** (API keys, Cognito, or IAM)
2. **Set up CloudWatch alarms** for errors and latency
3. **Configure custom domain** for API Gateway
4. **Enable AWS X-Ray** for distributed tracing
5. **Review and adjust throttling limits**
6. **Set up backup for DynamoDB tables**
7. **Implement proper error handling and retry logic**
8. **Add comprehensive logging and monitoring**
9. **Review IAM permissions** (principle of least privilege)
10. **Set up CI/CD pipeline** for automated deployments

## Next Steps

- Add more cities and offices to OfficesTable
- Create templates for additional categories
- Implement authentication and authorization
- Add rate limiting per user
- Set up monitoring dashboards
- Implement caching for frequently accessed data
