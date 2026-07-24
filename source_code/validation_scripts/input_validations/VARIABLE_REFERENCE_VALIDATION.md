# Variable Reference Validator

Validates variable reference integrity in `variables/{env}/{env}.json` files to prevent deployment issues.

## What It Validates

### ❌ Errors (Block Merge)

1. **Self-References (ISSUE #2)**
   ```json
   {
     "BaseUrl": "https://${BaseUrl}/api"
   }
   ```
   ❌ Variable references itself → infinite recursion

2. **Circular References (ISSUE #1)**
   ```json
   {
     "VarA": "${VarB}",
     "VarB": "${VarA}"
   }
   ```
   ❌ Variables reference each other in a loop

### ⚠️ Warnings (Allow But Report)

3. **Nested References (ISSUE #4)**
   ```json
   {
     "Config": {
       "url": "${ApiDomain}"
     }
   }
   ```
   ⚠️ References in nested objects/arrays are NOT resolved

### ℹ️ Information (Track Only)

4. **External References (ISSUE #3)**
   ```json
   {
     "SgId": "${ServerlessSgId}"
   }
   ```
   ℹ️ Variable will be resolved from stack outputs (OK if exists)

## Usage

### Local Validation

```bash
# Validate all variable files
python source_code/validation_scripts/input_validations/variable_reference_validator.py variables/

# Expected structure:
# variables/
#   dev/
#     dev.json
#   test/
#     test.json
#   prod/
#     prod.json
```

### CI/CD Integration

The validator runs automatically on:
- Pull requests that modify `variables/**/*.json`
- Pushes to main/develop branches
- Manual workflow dispatch

See `.github/workflows/validate-variables.yml`

### Exit Codes

- `0` - Validation passed
- `1` - Validation failed (errors found)

## Examples

### ✅ Valid Configuration

```json
{
  "Environment": "Dev",
  "Project": "LOS",
  "ApiDomain": "losdevapi.cyncsoftware.com",
  "Protocol": "https",
  "BaseUrl": "${Protocol}://${ApiDomain}",
  "InferenceEcsVariables": "API_DOMAIN:${ApiDomain},PROJECT:${Project}",
  "ServerlessSgId": "${ServerlessSgId}"
}
```

**Resolution Flow:**
1. Internal: `BaseUrl` = `"https://losdevapi.cyncsoftware.com"`
2. Internal: `InferenceEcsVariables` = `"API_DOMAIN:losdevapi.cyncsoftware.com,PROJECT:LOS"`
3. External: `ServerlessSgId` resolved from stack outputs

### ❌ Invalid - Self-Reference

```json
{
  "BaseUrl": "https://${BaseUrl}/api"
}
```

**Error:**
```
❌ ERROR: variables/dev/dev.json: Variable 'BaseUrl' references itself: https://${BaseUrl}/api
  This will cause infinite recursion and value corruption.
```

### ❌ Invalid - Circular Reference

```json
{
  "ServiceA": "${ServiceB}-backend",
  "ServiceB": "${ServiceA}-frontend"
}
```

**Error:**
```
❌ ERROR: variables/dev/dev.json: Circular reference detected: ServiceA -> ServiceB -> ServiceA
  These variables reference each other in a loop.
```

### ⚠️ Warning - Nested Reference

```json
{
  "ApiDomain": "api.com",
  "Config": {
    "endpoints": {
      "api": "https://${ApiDomain}"
    }
  }
}
```

**Warning:**
```
⚠️ WARNING: variables/dev/dev.json: Variable 'Config' has nested reference at 'endpoints.api': https://${ApiDomain}
  Nested references in objects/arrays are NOT resolved by the current implementation.
  Consider flattening the structure or moving the reference to the top level.
```

**Recommended Fix:**
```json
{
  "ApiDomain": "api.com",
  "ApiEndpoint": "https://${ApiDomain}",
  "Config": {
    "endpoints": {
      "api": "${ApiEndpoint}"
    }
  }
}
```

## Validation Rules

### 1. Self-Reference Check
- Variable cannot reference itself
- Prevents: `"Var": "${Var}"`
- Severity: **ERROR**

### 2. Circular Reference Detection
- Uses DFS graph traversal to detect cycles
- Detects chains like: `A → B → C → A`
- Severity: **ERROR**

### 3. Unresolvable Reference Check
- Identifies references to non-existent internal variables
- These will be attempted from stack outputs (OK if they exist there)
- Severity: **INFO**

### 4. Nested Reference Detection
- Scans nested objects/arrays for `${Variable}` patterns
- Current implementation doesn't resolve nested references
- Severity: **WARNING**

## Integration with Deployment

This validator ensures variables are safe **before** the deployment script processes them:

```
┌─────────────────────────────────────┐
│ 1. Pre-Merge Validation (CI/CD)    │
│    - Check self-references          │
│    - Check circular references      │
│    - Warn about nested refs         │
└──────────────┬──────────────────────┘
               │ ✅ Pass
               ▼
┌─────────────────────────────────────┐
│ 2. Deployment Script                │
│    - Load user variables            │
│    - Resolve internal refs          │
│    - Load stack outputs             │
│    - Resolve external refs          │
│    - Deploy stacks                  │
└─────────────────────────────────────┘
```

## Troubleshooting

### No files found
```
⚠️ WARNING: No variable files found in variables/
Expected structure: variables/{env}/{env}.json
```

**Fix:** Ensure files follow naming convention: `variables/dev/dev.json`

### JSON parsing error
```
❌ ERROR: variables/dev/dev.json: Invalid JSON format: Expecting ',' delimiter
```

**Fix:** Validate JSON syntax using `jsonlint` or VS Code

### Validation passes but deployment fails
- External references might not exist in stack outputs
- Check CloudWatch logs for missing variable errors
- Ensure stack outputs are published to S3

## Development

### Adding New Validations

1. Add validation method to `VariableReferenceValidator` class
2. Call it in `validate_variable_file()` method
3. Add test cases and documentation
4. Update this README

### Testing

Create test variable files:

```bash
# Test self-reference
echo '{"Var": "${Var}"}' > test-self-ref.json
python variable_reference_validator.py test-self-ref.json

# Test circular reference
echo '{"A": "${B}", "B": "${A}"}' > test-circular.json
python variable_reference_validator.py test-circular.json
```

## Related Documentation

- [Deployment Script](../../code_deploy/custom_actions_infra/cus_stack_deploy/cus_stack_deploy.py)
- [Variable Resolution Flow](../../code_deploy/custom_actions_infra/cus_stack_deploy/README.md)
- [Jinja2 Utilities](../jinja2_utils/jinja2_utils.py)
