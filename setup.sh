#!/bin/bash
# Setup script for Unix/macOS systems

echo "Setting up Kiro Backend Civic Assistant..."

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 is required but not found."
    echo "Please install Python 3.11 and try again."
    exit 1
fi

echo "Python 3.11 found."

# Create virtual environment
echo "Creating virtual environment..."
python3.11 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements-dev.txt

echo ""
echo "Setup complete!"
echo ""

# Check if SEED flag is set
if [ "${SEED}" = "true" ]; then
    echo "SEED=true detected. Seeding DynamoDB tables..."
    echo ""
    
    # Check if AWS CLI is configured
    if ! command -v aws &> /dev/null; then
        echo "Warning: AWS CLI not found. Skipping seeding."
        echo "Install AWS CLI and configure credentials to enable seeding."
    else
        # Check if tables exist (requires deployment first)
        echo "Checking if DynamoDB tables exist..."
        if aws dynamodb describe-table --table-name OfficesTable &> /dev/null; then
            echo "Running seed script..."
            python scripts/seed_dynamodb.py
            echo ""
        else
            echo "Warning: DynamoDB tables not found."
            echo "Please deploy the SAM template first:"
            echo "  sam build"
            echo "  sam deploy --guided"
            echo ""
            echo "Then run seeding with:"
            echo "  SEED=true bash setup.sh"
            echo ""
        fi
    fi
else
    echo "To seed DynamoDB tables after deployment, run:"
    echo "  SEED=true bash setup.sh"
    echo ""
    echo "Or manually run:"
    echo "  python scripts/seed_dynamodb.py"
    echo ""
fi

echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest tests/"
echo ""
