#!/bin/bash

set -e

TEMPLATE_FILE="template.yml"

# Check if EXECUTION_ID is set
if [ -z "$EXECUTION_ID" ]; then
  echo "Error: EXECUTION_ID environment variable is not set."
  exit 0
fi

# Ensure template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "Error: $TEMPLATE_FILE does not exist."
  exit 0
fi

# Detect and update Description
if grep -q '^Description:[[:space:]]*">-' "$TEMPLATE_FILE" || grep -q '^Description:[[:space:]]*>-' "$TEMPLATE_FILE"; then
  # Multiline block-style description detected
  START_LINE=$(grep -n '^Description:[[:space:]]*>-' "$TEMPLATE_FILE" | cut -d':' -f1)
  NEXT_LINE=$((START_LINE + 1))

  # Capture existing multiline content until a non-indented line
  DESC_LINES=()
  while IFS= read -r LINE; do
    [[ "$LINE" =~ ^[[:space:]] ]] || break
    DESC_LINES+=("$LINE")
  done < <(tail -n +"$NEXT_LINE" "$TEMPLATE_FILE")

  # Reconstruct cleaned description
  CLEAN_DESC=$(printf "%s " "${DESC_LINES[@]}" | sed 's/[[:space:]]\+/ /g' | sed 's/[[:space:]]$//')

  # Replace entire block with new one including execution ID
  {
    head -n "$((START_LINE - 1))" "$TEMPLATE_FILE"
    echo "Description: >-"
    echo "  ${CLEAN_DESC} - Execution ID: $EXECUTION_ID"
    # Skip old description block
    tail -n +"$NEXT_LINE" "$TEMPLATE_FILE" | sed -n "/^[^[:space:]]/,\$p"
  } > "${TEMPLATE_FILE}.tmp" && mv "${TEMPLATE_FILE}.tmp" "$TEMPLATE_FILE"

elif grep -q '^Description:' "$TEMPLATE_FILE"; then
  # Inline description
  CURRENT_DESC=$(grep '^Description:' "$TEMPLATE_FILE" | sed 's/^Description:[[:space:]]*//')
  CLEAN_DESC=$(echo "$CURRENT_DESC" | sed 's/^"\(.*\)"$/\1/')
  sed -i "s|^Description:.*|Description: \"${CLEAN_DESC} - Execution ID: $EXECUTION_ID\"|" "$TEMPLATE_FILE"
else
  # No description exists; insert at top
  sed -i "1i Description: \"Service stack - Execution ID: $EXECUTION_ID\"" "$TEMPLATE_FILE"
fi

echo "Template description updated successfully with Execution ID: $EXECUTION_ID"
