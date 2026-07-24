"""
Variable Resolver Utility

This module provides regex-based variable resolution for strings containing ${VarName} patterns.
"""

import re
import logging

logger = logging.getLogger(__name__)


def resolve_variables(text, variables_dict):
    """
    Resolve all ${VarName} patterns in text using provided variables dictionary.
    
    Args:
        text (str or dict): Text or dictionary containing ${VarName} patterns to resolve
        variables_dict (dict): Dictionary with variable names and their values
    
    Returns:
        str or dict: Text/dict with all variables resolved
        
    Raises:
        ValueError: If a variable reference is found but not in variables_dict
    """
    if text is None:
        return None
    
    # Handle dict recursively
    if isinstance(text, dict):
        return {key: resolve_variables(value, variables_dict) for key, value in text.items()}
    
    # Handle list recursively
    if isinstance(text, list):
        return [resolve_variables(item, variables_dict) for item in text]
    
    # Convert to string if not already
    text = str(text)
    
    # Pattern to match ${VarName}
    pattern = r'\$\{([^}]+)\}'
    
    # Find all variable references
    matches = re.findall(pattern, text)
    
    # Check if all variables exist in variables_dict
    missing_vars = [var for var in matches if var not in variables_dict]
    if missing_vars:
        error_msg = f"Missing variables in variables_dict: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Replace all ${VarName} with actual values
    def replace_var(match):
        var_name = match.group(1)
        var_value = variables_dict.get(var_name, '')
        logger.debug(f"Resolving ${{{var_name}}} -> {var_value}")
        return str(var_value)
    
    resolved_text = re.sub(pattern, replace_var, text)
    
    return resolved_text


def find_variables(text):
    """
    Find all ${VarName} patterns in text.
    
    Args:
        text (str or dict): Text or dictionary to search for variables
    
    Returns:
        list: List of unique variable names found
    """
    if text is None:
        return []
    
    # Handle dict recursively
    if isinstance(text, dict):
        all_vars = []
        for value in text.values():
            all_vars.extend(find_variables(value))
        return list(set(all_vars))
    
    # Handle list recursively
    if isinstance(text, list):
        all_vars = []
        for item in text:
            all_vars.extend(find_variables(item))
        return list(set(all_vars))
    
    # Convert to string if not already
    text = str(text)
    
    # Pattern to match ${VarName}
    pattern = r'\$\{([^}]+)\}'
    
    # Find all variable references
    matches = re.findall(pattern, text)
    
    return list(set(matches))
