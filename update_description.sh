#!/bin/bash

set -e

TEMPLATE_FILE="template.yml"

# Check if EXECUTION_ID is set
if [ -z "$EXECUTION_ID" ]; then
  echo "Error: EXECUTION_ID environment variable is not set."
  exit 1
fi

# Ensure template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "Error: $TEMPLATE_FILE does not exist."
  exit 1
fi

# Check if 'Description:' key exists
if grep -q '^Description:' "$TEMPLATE_FILE"; then
  # Append execution ID to existing description
  sed -i "s|^Description:.*|& - Execution ID: $EXECUTION_ID|" "$TEMPLATE_FILE"
else
  # Insert description at the top
  sed -i "1i Description: \"Service stack - Execution ID: $EXECUTION_ID\"" "$TEMPLATE_FILE"
fi

echo "Template description updated successfully with Execution ID: $EXECUTION_ID"
