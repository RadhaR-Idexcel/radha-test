"""
Input validation functions for various modules to ensure required inputs are provided
and correctly formatted.
"""
import os
from logger_config import get_logger



# Local variable declarations
logger = get_logger(__name__)



def validate_input_keys(input_list, required_keys):
    """
    Validate that all required keys are present in the input.

    Args:
        input_data (dict | list | set): The incoming data or its keys.
        required_keys (list | set): Keys expected to be present.

    Raises:
        ValueError: If any required keys are missing (lists all missing keys).

    Returns:
        bool: True if all required keys are present.
    """
    if not isinstance(input_list, (list, dict)):
        raise TypeError("Input data must be a list or dict.")

    if not isinstance(required_keys, (list)):
        raise TypeError("Required keys must be a list.")

    missing_fields = [field for field in required_keys if field not in input_list]
    if missing_fields:
        missing_str = ', '.join(missing_fields)
        error_msg = f'Missing required fields: [{missing_str}]. Input validation failed.'
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info('All required keys are present.')
    return True


def validate_environment_variables(required_env_vars):
    """
    Validate that all required environment variables are set and return them as a dictionary.

    Args:
        required_env_vars (list): List of required environment variable names.

    Returns:
        dict: Dictionary containing environment variable names and their values.

    Raises:
        ValueError: If any required environment variable is not set.
    """
    if not isinstance(required_env_vars, list):
        raise TypeError("Required environment variables must be a list.")
    
    env_vars = {}
    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            error_msg = f"Required environment variable not set: {var}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        env_vars[var] = value
        logger.info(f"{var}: {value}")
    
    logger.info('All required environment variables are set.')
    return env_vars
