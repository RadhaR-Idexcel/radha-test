#!/bin/bash

set -e

# Variables
CODE_BASE_DIR=${1:-"code_base/lambdas"}

echo "========================================="
echo "Lambda Requirements Installation Script"
echo "========================================="
echo ""

# Check if code_base directory exists
if [ ! -d "$CODE_BASE_DIR" ]; then
    echo "Error: Directory '$CODE_BASE_DIR' not found"
    exit 1
fi
echo "Current working dir:`pwd`"
echo "Searching for requirements.txt files in $CODE_BASE_DIR..."
echo ""

# Find all requirements.txt files in lambdas directory
requirements_files=$(find "$CODE_BASE_DIR" -type f -name "requirements.txt")

if [ -z "$requirements_files" ]; then
    echo "Warning: No requirements.txt files found in $CODE_BASE_DIR"
    exit 0
fi

# Process each requirements.txt file
for req_file in $requirements_files; do
    req_dir=$(dirname "$req_file")
    
    echo "----------------------------------------"
    echo "Processing: $req_file"
    echo "Target directory: $req_dir"
    echo "----------------------------------------"
    
    # Install requirements
    echo "Installing requirements..."
    if ! pip install -r "$req_file" -t "$req_dir" >> stdout.log 2>&1; then
        echo "ERROR: Failed to install requirements from $req_file"
        echo "Check stdout.log for details"
        exit 1
    fi
    
    # Remove __pycache__ directories
    echo "Removing __pycache__ directories..."
    find "$req_dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove .dist-info directories
    echo "Removing *.dist-info directories..."
    find "$req_dir" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
    
    echo "Completed: $req_dir"
    echo ""
done

echo "========================================="
echo "All requirements installed successfully"
echo "========================================="