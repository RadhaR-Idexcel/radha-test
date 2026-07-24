# Validation Scripts

Table of Contents for input validation scripts and documentation.

## Input Validations

### Variable Reference Validation
**Purpose:** Validates variable reference integrity in environment variable files before deployment.

**Documentation:** [Variable Reference Validation Guide](input_validations/VARIABLE_REFERENCE_VALIDATION.md)

**Script:** [`variable_reference_validator.py`](input_validations/variable_reference_validator.py)

**What it validates:
- ❌ Self-references (blocks merge)
- ❌ Circular references (blocks merge)
- ⚠️  Nested references (warning only)
- ℹ️  External references (informational)

**Usage:**
```bash
python source_code/validation_scripts/input_validations/variable_reference_validator.py variables/
```

**GitHub Workflow:** `.github/workflows/validate-variables.yml`

---

## Adding New Validation Scripts

1. Create script in appropriate subdirectory
2. Add detailed documentation
3. Update this README with table of contents entry
4. Create GitHub Actions workflow if needed

## Directory Structure

```
validation_scripts/
├── README.md (this file - table of contents only)
├── input_validations/
│   ├── variable_reference_validator.py
│   └── VARIABLE_REFERENCE_VALIDATION.md (detailed guide)
└── (future validation categories)/
```

## Related Documentation

- [Deployment Script](../code_deploy/custom_actions_infra/cus_stack_deploy/cus_stack_deploy.py)
- [Variable Resolution Flow](../code_deploy/custom_actions_infra/cus_stack_deploy/)
- [GitHub Actions Workflows](../../.github/workflows/)
