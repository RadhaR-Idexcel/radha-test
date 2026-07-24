# Reusable Utilities

## Overview

This directory contains reusable utility modules for AWS services, file operations, logging, and common functions. These utilities are designed for **code reuse only** and should not contain business logic.

## Purpose

- Provide standardized interfaces for AWS services
- Centralize common operations (file I/O, validation, logging)
- Reduce code duplication across deployment scripts
- Maintain consistent error handling and logging patterns

---

## ⚠️ Important Guidelines

### What Belongs in Utils

✅ **Generic, reusable code:**
- AWS service client wrappers (S3, ECR, CloudFormation, etc.)
- File operations (read, write, JSON/YAML parsing)
- Logging configuration
- Input validation helpers
- Template rendering utilities

### What Does NOT Belong in Utils

❌ **Business logic:**
- Stack deployment workflows
- Image import logic
- Environment-specific configurations
- Pipeline orchestration
- Deployment decision logic

### Rule of Thumb

> If it's specific to **how your application works**, it belongs in scripts.  
> If it's a **generic helper function** that could be used anywhere, it belongs in utils.

---

## Directory Structure

```
utils/
├── aws/                          # AWS service wrappers
│   ├── cloudformation/
│   │   ├── cloudformation.py     # CloudFormation operations
│   │   └── setup.py
│   ├── ecr/
│   │   ├── ecr.py                # ECR repository management
│   │   └── setup.py
│   ├── pipeline/
│   │   ├── pipeline.py           # CodePipeline operations
│   │   └── setup.py
│   ├── s3/
│   │   ├── s3.py                 # S3 bucket operations
│   │   └── setup.py
│   ├── ssm/
│   │   ├── ssm.py                # SSM Parameter Store
│   │   └── setup.py
│   └── sts/
│       ├── sts.py                # STS assume role
│       └── setup.py
├── common/                       # Common utilities
│   ├── file_operations/
│   │   ├── file_operations.py    # Read/write files
│   │   └── setup.py
│   ├── jinja2_utils/
│   │   ├── jinja2_utils.py       # Template rendering
│   │   └── setup.py
│   ├── logger_config/
│   │   ├── logger_config.py      # Centralized logging
│   │   └── setup.py
│   └── validation/
│       ├── validation.py         # Input validation helpers
│       └── setup.py
└── install_requirements.sh       # Install all utility dependencies
```

---

## Available Utilities

### AWS Service Wrappers

#### CloudFormation (`aws/cloudformation`)
```python
from cloudformation import CloudFormationClient

cf_client = CloudFormationClient()
cf_client.create_or_update_stack(
    stack_name="my-stack",
    template_body=template,
    parameters=params,
    capabilities=["CAPABILITY_NAMED_IAM"]
)
```

#### ECR (`aws/ecr`)
```python
from ecr import ECRClient

ecr_client = ECRClient()
ecr_client.create_repository_if_not_exists(repository_name="my-repo")
ecr_client.put_lifecycle_policy(repository_name="my-repo", policy=policy)
```

#### S3 (`aws/s3`)
```python
from s3 import S3Client

s3_client = S3Client()
s3_client.upload_file(file_path="data.json", bucket="my-bucket", key="path/data.json")
content = s3_client.download_file_as_string(bucket="my-bucket", key="path/data.json")
```

#### SSM (`aws/ssm`)
```python
from ssm import SSMClient

ssm_client = SSMClient()
ssm_client.put_parameter(name="/app/config", value="value", parameter_type="String")
value = ssm_client.get_parameter(name="/app/config")
```

#### STS (`aws/sts`)
```python
from sts import STSClient

sts_client = STSClient()
credentials = sts_client.assume_role(
    role_arn="arn:aws:iam::123456789012:role/MyRole",
    session_name="MySession"
)
```

---

### Common Utilities

#### File Operations (`common/file_operations`)
```python
from file_operations import read_file, write_file

content = read_file("config.json")
write_file("output.json", content)
```

#### Jinja2 Template Rendering (`common/jinja2_utils`)
```python
from jinja2_utils import render_string, render_template

result = render_string("Hello ${name}", {"name": "World"})
# Result: "Hello World"

template_content = render_template("template.yml", variables)
```

#### Logger Configuration (`common/logger_config`)
```python
from logger_config import get_logger

logger = get_logger("my_module")
logger.info("Information message")
logger.error("Error message")
logger.debug("Debug message")
```

#### Input Validation (`common/validation`)
```python
from validation import validate_input_keys, validate_environment_variables

# Validate required keys in dictionary
validate_input_keys(data, required_keys=["name", "value"])

# Validate environment variables
validate_environment_variables(["AWS_REGION", "ENV_NAME"])
```

---

## Installation

### Install All Utils

```bash
cd source_code/utils
./install_requirements.sh
```

### Install Specific Util

```bash
cd source_code/utils/aws/s3
pip install -e .
```

---

## Usage in Scripts

### Import from Utils

```python
import sys
from pathlib import Path

# Add utils to Python path
utils_path = Path(__file__).parent.parent / "utils"
sys.path.insert(0, str(utils_path))

# Import utilities
from logger_config import get_logger
from s3 import S3Client
from validation import validate_environment_variables

# Use utilities
logger = get_logger(__name__)
s3_client = S3Client()
validate_environment_variables(["ENV_NAME", "BUCKET_NAME"])
```

---

## Creating New Utilities

### 1. Determine Location

- AWS service wrapper → `utils/aws/{service}/`
- Generic helper → `utils/common/{category}/`

### 2. Create Module Structure

```
utils/aws/dynamodb/
├── dynamodb.py
├── setup.py
└── requirements.txt (if needed)
```

### 3. Implement Client Class

```python
# dynamodb.py
import boto3
from logger_config import get_logger

logger = get_logger(__name__)

class DynamoDBClient:
    def __init__(self, **kwargs):
        self.client = boto3.client('dynamodb', **kwargs)
    
    def put_item(self, table_name, item):
        """Put item in DynamoDB table."""
        logger.info(f"Putting item in table: {table_name}")
        response = self.client.put_item(
            TableName=table_name,
            Item=item
        )
        return response
```

### 4. Create setup.py

```python
from setuptools import setup, find_packages

setup(
    name="dynamodb-utils",
    version="1.0.0",
    py_modules=["dynamodb"],
    install_requires=[
        "boto3>=1.26.0",
    ],
)
```

### 5. Document Usage

Add example to this README.

---

## Best Practices

### ✅ Do's

- Keep utilities **stateless** when possible
- Use **consistent error handling** patterns
- Add **comprehensive logging**
- Write **docstrings** for all public methods
- Make utilities **configurable** via parameters
- Handle **AWS credential errors** gracefully

### ❌ Don'ts

- Don't hardcode **environment-specific values**
- Don't include **business logic**
- Don't create **circular dependencies**
- Don't use **global state** (except logger)
- Don't add **deployment workflows** here

---

## Testing Utilities

### Manual Testing

```python
# test_s3.py
from s3 import S3Client

s3_client = S3Client()
s3_client.upload_file("test.txt", "my-bucket", "test.txt")
print("Upload successful!")
```

### Usage in Scripts

Import and use in deployment scripts to verify functionality.

---

## Maintenance

### Adding Dependencies

1. Add to util's `requirements.txt`
2. Update `install_requirements.sh` if needed
3. Test installation in clean environment

### Updating Utilities

1. Maintain **backward compatibility** when possible
2. Update version in `setup.py`
3. Document breaking changes
4. Update usage examples in this README

---

## Related Documentation

- [Stack Deployment](../code_deploy/custom_actions_infra/cus_stack_deploy/README.md)
- [ECR Image Management](../code_deploy/custom_actions_infra/import_ecr_images/README.md)
- [Validation Scripts](../validation_scripts/README.md)
