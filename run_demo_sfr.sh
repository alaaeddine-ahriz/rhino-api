#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup virtual environment
cleanup() {
    print_status "Cleaning up virtual environment..."
    if [ -d "venv" ]; then
        rm -rf venv
        print_success "Virtual environment deleted"
    else
        print_warning "Virtual environment directory not found"
    fi
}

# Set up trap to cleanup on script exit (success or failure)
trap cleanup EXIT

# Check if Python 3.11 is available
PYTHON_CMD=""
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    # Check if python3 is version 3.11
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -o '3\.11')
    if [ "$PYTHON_VERSION" = "3.11" ]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    print_error "Python 3.11 is not installed or not in PATH"
    print_error "Please install Python 3.11 and try again"
    print_error "You can install it with: brew install python@3.11 (on macOS)"
    exit 1
fi

print_status "Python 3.11 found: $($PYTHON_CMD --version)"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in current directory"
    exit 1
fi

print_status "requirements.txt found"

# Check if the test script exists
if [ ! -f "mail/demo-sfr.py" ]; then
    print_error "mail/demo-sfr.py not found"
    exit 1
fi

print_status "Test script found: mail/demo-sfr.py"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found"
    print_error "Please create a .env file with your configuration"
    print_error "You can copy from .env.example if available"
    exit 1
fi

print_status ".env file found"

# Create virtual environment with Python 3.11
print_status "Creating virtual environment with Python 3.11..."
$PYTHON_CMD -m venv venv

if [ $? -ne 0 ]; then
    print_error "Failed to create virtual environment"
    exit 1
fi

print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

print_success "Virtual environment activated"

# Verify we're using Python 3.11 in the venv
VENV_PYTHON_VERSION=$(python --version 2>&1)
print_status "Virtual environment Python version: $VENV_PYTHON_VERSION"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

if [ $? -ne 0 ]; then
    print_warning "Failed to upgrade pip, continuing anyway..."
fi

# Install requirements
print_status "Installing requirements..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Failed to install requirements"
    exit 1
fi

print_success "Requirements installed successfully"

# Run the test script
print_status "Running test script..."
print_status "Note: The script will prompt for timeout input"
echo ""

# Show current directory and Python path for debugging
print_status "Current working directory: $(pwd)"
print_status "Python path: $PYTHONPATH"

# Ensure we're in the project root directory
if [ ! -d "app" ]; then
    print_error "app directory not found. Please run this script from the project root directory."
    exit 1
fi

# Set PYTHONPATH to include current directory for proper imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
print_status "Updated Python path: $PYTHONPATH"

# Set the API port environment variable
export PORT=8000

# Run the script from the project root directory to ensure proper imports
python mail/demo-sfr.py

# Capture the exit code
script_exit_code=$?

echo ""
if [ $script_exit_code -eq 0 ]; then
    print_success "Test script completed successfully"
else
    print_error "Test script failed with exit code $script_exit_code"
fi

# Deactivate virtual environment
print_status "Deactivating virtual environment..."
deactivate

print_success "Virtual environment deactivated"

# The cleanup function will be called automatically due to the trap
print_status "Script execution completed"

exit $script_exit_code 