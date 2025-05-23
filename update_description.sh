#!/bin/bash
set -e

TEMPLATE_FILE="template.yml"

# Check if EXECUTION_ID is set
if [ -z "$EXECUTION_ID" ]; then
  echo "ERROR: EXECUTION_ID is not set."
  exit 1
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "ERROR: $TEMPLATE_FILE not found."
  exit 1
fi

# Check if Description key exists
if grep -q '^Description:' "$TEMPLATE_FILE"; then
  # Description exists, append Execution ID if not already present
  sed -i "/^Description:/ s|\"$| - Execution ID: $EXECUTION_ID\"|" "$TEMPLATE_FILE"
  sed -i "/^Description:/ s|Execution ID: .*Execution ID:|Execution ID:|g" "$TEMPLATE_FILE"  # Cleanup duplicates
else
  # No description found, insert after the first non-empty line
  awk -v eid="$EXECUTION_ID" '
    BEGIN { inserted=0 }
    NF && !inserted {
      print
      print "Description: \"Service stack - Execution ID: " eid "\""
      inserted=1
      next
    }
    { print }
  ' "$TEMPLATE_FILE" > tmp_template.yml && mv tmp_template.yml "$TEMPLATE_FILE"
fi

echo "Template description updated successfully."
