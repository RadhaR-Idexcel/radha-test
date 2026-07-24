"""
Variable Loading and Resolution Utility

This module provides functionality to load variables from environment-specific JSON files
and recursively resolve internal variable references using ${VariableName} syntax.

Features:
- Loads variables from {account}/variables/{env}/{env}.json
- Recursively resolves ${Variable} references up to 10 iterations
- Logs warnings for unresolved variables instead of failing
- No S3 stack output loading (simplified from cus_stack_deploy.py)

Usage:
    from variable_loader import load_and_resolve_variables
    
    variables = load_and_resolve_variables(
        env_name='Dev',
        account_name='application_account'
    )
"""

import os
import json
import re
from pathlib import Path
from logger_config import get_logger

# Initialize logger
logger = get_logger(os.path.splitext(os.path.basename(__file__))[0])

# Constants
MAX_RESOLUTION_ITERATIONS = 10
VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')


def load_variables_from_file(env_name, account_name):
    """
    Load variables from {account}/variables/{env}/{env}.json.
    
    Args:
        env_name (str): Environment name (e.g., 'Dev', 'Test', 'Prod').
        account_name (str): Account folder name (e.g., 'application_account').
    
    Returns:
        dict: Variables dictionary loaded from file.
    
    Raises:
        FileNotFoundError: If variable file doesn't exist.
        json.JSONDecodeError: If file contains invalid JSON.
    """
    env_lower = env_name.lower()
    variable_file_path = f'{account_name}/variables/{env_lower}/{env_lower}.json'
    
    logger.info(f"Loading variables from: {variable_file_path}")
    
    if not os.path.exists(variable_file_path):
        error_msg = f"Variable file not found: {variable_file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    with open(variable_file_path, 'r', encoding='utf-8') as f:
        variables = json.load(f)
    
    logger.info(f"Successfully loaded {len(variables)} variables for environment: {env_name}")
    return variables


def find_variable_references(value):
    """
    Find all ${VariableName} references in a string value.
    
    Args:
        value: Value to search (string, dict, list, or other).
    
    Returns:
        set: Set of variable names found in the value.
    """
    if isinstance(value, str):
        matches = VARIABLE_PATTERN.findall(value)
        return set(matches)
    elif isinstance(value, dict):
        refs = set()
        for v in value.values():
            refs.update(find_variable_references(v))
        return refs
    elif isinstance(value, list):
        refs = set()
        for item in value:
            refs.update(find_variable_references(item))
        return refs
    else:
        return set()


def resolve_value(value, variables, unresolved_vars):
    """
    Resolve ${VariableName} references in a single value.
    
    Args:
        value: Value to resolve (string, dict, list, or other).
        variables (dict): Dictionary of available variables.
        unresolved_vars (set): Set to track unresolved variable names.
    
    Returns:
        Resolved value with ${Variable} references replaced.
    """
    if isinstance(value, str):
        # Find all variable references
        matches = VARIABLE_PATTERN.findall(value)
        
        if not matches:
            return value
        
        resolved = value
        for var_name in matches:
            if var_name in variables:
                replacement = str(variables[var_name])
                resolved = resolved.replace(f'${{{var_name}}}', replacement)
            else:
                # Variable not found - track it
                unresolved_vars.add(var_name)
        
        return resolved
    
    elif isinstance(value, dict):
        return {k: resolve_value(v, variables, unresolved_vars) for k, v in value.items()}
    
    elif isinstance(value, list):
        return [resolve_value(item, variables, unresolved_vars) for item in value]
    
    else:
        # Return non-string values as-is
        return value


def resolve_variables_recursively(variables):
    """
    Recursively resolve ${Variable} references in the variables dictionary.
    
    Performs up to MAX_RESOLUTION_ITERATIONS iterations to resolve nested references.
    For example, if:
        EnvNameSmall = "dev"
        CodatBucketName = "los-${EnvNameSmall}-codat-bkt"
    
    First iteration resolves CodatBucketName to "los-dev-codat-bkt".
    Multiple iterations handle cases where resolved values contain more references.
    
    Args:
        variables (dict): Variables dictionary to resolve.
    
    Returns:
        dict: Fully resolved variables dictionary.
    """
    logger.info("Starting recursive variable resolution...")
    
    resolved_vars = dict(variables)
    all_unresolved = set()
    
    for iteration in range(1, MAX_RESOLUTION_ITERATIONS + 1):
        logger.debug(f"Resolution iteration {iteration}/{MAX_RESOLUTION_ITERATIONS}")
        
        # Track unresolved variables in this iteration
        iteration_unresolved = set()
        
        # Create new resolved dictionary
        new_resolved = {}
        
        for key, value in resolved_vars.items():
            new_resolved[key] = resolve_value(value, resolved_vars, iteration_unresolved)
        
        # Check if any changes were made
        if new_resolved == resolved_vars:
            logger.info(f"Variable resolution completed after {iteration} iteration(s)")
            break
        
        resolved_vars = new_resolved
        all_unresolved.update(iteration_unresolved)
    else:
        # Reached max iterations
        logger.warning(f"Variable resolution stopped after {MAX_RESOLUTION_ITERATIONS} iterations")
    
    # Log warnings for any unresolved variables
    if all_unresolved:
        logger.warning(f"Found {len(all_unresolved)} unresolved variable reference(s): {sorted(all_unresolved)}")
        logger.warning("These variables are referenced but not defined in the variable file")
        logger.warning("Unresolved references will remain as ${VariableName} in the output")
    else:
        logger.info("All variable references successfully resolved")
    
    return resolved_vars


def load_and_resolve_variables(env_name, account_name):
    """
    Load variables from file and recursively resolve ${Variable} references.
    
    This is a consolidated utility that replaces duplicate load_variables() functions
    across multiple deployment scripts. It provides:
    
    1. Variable file loading from {account}/variables/{env}/{env}.json
    2. Recursive resolution of ${Variable} references (up to 10 iterations)
    3. Warning logs for unresolved variables (does not fail)
    
    Simplified from cus_stack_deploy.py - does NOT load stack outputs from S3.
    
    Args:
        env_name (str): Environment name (e.g., 'Dev', 'Test', 'Prod').
        account_name (str): Account folder name (e.g., 'application_account', 'deployment_account').
    
    Returns:
        dict: Fully resolved variables dictionary.
    
    Raises:
        FileNotFoundError: If variable file doesn't exist.
        json.JSONDecodeError: If variable file contains invalid JSON.
    
    Examples:
        >>> # Load and resolve variables for Dev environment
        >>> variables = load_and_resolve_variables('Dev', 'application_account')
        >>> 
        >>> # If variable file contains:
        >>> # {
        >>> #   "EnvNameSmall": "dev",
        >>> #   "CodatBucketName": "los-${EnvNameSmall}-codat-bkt"
        >>> # }
        >>> # 
        >>> # Result will be:
        >>> # {
        >>> #   "EnvNameSmall": "dev",
        >>> #   "CodatBucketName": "los-dev-codat-bkt"
        >>> # }
    """
    logger.info(f"Loading and resolving variables for env={env_name}, account={account_name}")
    
    # Step 1: Load variables from file
    variables = load_variables_from_file(env_name, account_name)
    
    # Step 2: Recursively resolve variable references
    resolved_variables = resolve_variables_recursively(variables)
    
    logger.info(f"Variable loading and resolution completed. Total variables: {len(resolved_variables)}")
    
    return resolved_variables
