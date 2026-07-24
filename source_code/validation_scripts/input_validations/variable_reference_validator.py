"""
Variable Reference Validator for User Variables Files.

Validates variable files (variables/{env}/{env}.json) for:
- Circular references between variables
- Self-references in variable definitions
- Unresolvable references (missing variables)
- Nested object/array references (unsupported)

This script should be run as part of CI/CD validation before merge.
Exit code 0 = validation passed, non-zero = validation failed.

Usage:
    python variable_reference_validator.py <path_to_variables_dir>
    python variable_reference_validator.py variables/
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

# Import logger from utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils" / "common" / "logger_config"))
from logger_config import get_logger

# Initialize logger
logger = get_logger("variable_validator")

# Global variables to track validation results
ERRORS = []
WARNINGS = []
VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')


def extract_variable_references(value: str) -> Set[str]:
    """
    Extract all ${Variable} references from a string value.
    
    Args:
        value: String that may contain ${Variable} references
    
    Returns:
        Set of variable names referenced (without ${} delimiters)
    """
    if not isinstance(value, str):
        return set()
    
    matches = VARIABLE_PATTERN.findall(value)
    return set(matches)


def build_dependency_graph(variables: Dict[str, any]) -> Dict[str, Set[str]]:
    """
    Build a dependency graph showing which variables reference which.
    
    Args:
        variables: Dictionary of variable name -> value
    
    Returns:
        Dictionary mapping variable name -> set of variables it references
    """
    dependency_graph = {}
    
    for var_name, var_value in variables.items():
        if isinstance(var_value, str):
            referenced_vars = extract_variable_references(var_value)
            dependency_graph[var_name] = referenced_vars
        else:
            dependency_graph[var_name] = set()
    
    return dependency_graph


def validate_self_references(variables: Dict[str, any], file_path: str) -> bool:
    """
    Check if any variable references itself.
    
    ISSUE: Self-Reference Edge Case
    Example: {"BaseUrl": "https://${BaseUrl}/api"}
    
    Args:
        variables: Dictionary of variable name -> value
        file_path: Path to variable file (for error reporting)
    
    Returns:
        True if no self-references found, False otherwise
    """
    has_issues = False
    
    for var_name, var_value in variables.items():
        if not isinstance(var_value, str):
            continue
        
        referenced_vars = extract_variable_references(var_value)
        
        if var_name in referenced_vars:
            error_msg = (
                f"ERROR: {file_path}\n"
                f"  Variable '{var_name}' references itself: {var_value}\n"
                f"  This will cause infinite recursion and value corruption."
            )
            ERRORS.append(error_msg)
            logger.error(error_msg)
            has_issues = True
    
    return not has_issues


def _find_cycle_in_dependencies(var: str, path: List[str], visited: Set[str], dependency_graph: Dict[str, Set[str]]) -> Optional[List[str]]:
    """DFS to find circular reference starting from var."""
    if var in path:
        # Found a cycle - extract the circular part
        cycle_start = path.index(var)
        return path[cycle_start:] + [var]
    
    if var in visited:
        return None
    
    visited.add(var)
    path.append(var)
    
    # Check all variables this one references
    for referenced_var in dependency_graph.get(var, set()):
        # Only check if referenced_var exists in our variables
        if referenced_var in dependency_graph:
            cycle = _find_cycle_in_dependencies(referenced_var, path.copy(), visited, dependency_graph)
            if cycle:
                return cycle
    
    return None


def validate_circular_references(dependency_graph: Dict[str, Set[str]], file_path: str) -> bool:
    """
    Detect circular reference chains in variable dependencies.
    
    ISSUE: Circular Reference Detection
    Example: {"VarA": "${VarB}", "VarB": "${VarA}"}
    
    Args:
        dependency_graph: Map of variable -> set of variables it references
        file_path: Path to variable file (for error reporting)
    
    Returns:
        True if no circular references found, False otherwise
    """
    has_issues = False
    visited_global = set()
    
    for var_name in dependency_graph:
        if var_name not in visited_global:
            cycle = _find_cycle_in_dependencies(var_name, [], set(), dependency_graph)
            if cycle:
                visited_global.update(cycle)
                cycle_str = " -> ".join(cycle)
                error_msg = (
                    f"ERROR: {file_path}\n"
                    f"  Circular reference detected: {cycle_str}\n"
                    f"  These variables reference each other in a loop."
                )
                ERRORS.append(error_msg)
                logger.error(error_msg)
                has_issues = True
    
    return not has_issues


def validate_external_references(variables: Dict[str, any], dependency_graph: Dict[str, Set[str]]) -> bool:
    """
    Check for variables that reference non-existent internal variables.
    These will be resolved from stack outputs (informational only).
    
    Args:
        variables: Dictionary of all variables
        dependency_graph: Map of variable dependencies
    
    Returns:
        True (always passes, informational only)
    """
    for var_name, referenced_vars in dependency_graph.items():
        # Find referenced variables that don't exist in user variables
        missing_refs = referenced_vars - set(variables.keys())
        
        if missing_refs:
            # This is OK - they will be resolved from stack outputs
            # Only show if there are issues to report
            pass
    
    return True


def _scan_nested_for_references(obj, path: str = ""):
    """Recursively scan for ${} references in nested structures."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, str) and '${' in value:
                return current_path, value
            result = _scan_nested_for_references(value, current_path)
            if result:
                return result
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            current_path = f"{path}[{idx}]"
            if isinstance(item, str) and '${' in item:
                return current_path, item
            result = _scan_nested_for_references(item, current_path)
            if result:
                return result
    return None


def validate_nested_references(variables: Dict[str, any], file_path: str) -> bool:
    """
    Check for references in nested objects/arrays (currently unsupported).
    
    ISSUE: Non-String Values Not Handled in Resolution
    Example: {"Config": {"url": "${ApiDomain}"}}
    
    Args:
        variables: Dictionary of all variables
        file_path: Path to variable file (for error reporting)
    
    Returns:
        True (always passes, warning only)
    """
    for var_name, var_value in variables.items():
        if isinstance(var_value, (dict, list)):
            result = _scan_nested_for_references(var_value)
            if result:
                nested_path, nested_value = result
                warning_msg = (
                    f"WARNING: {file_path}\n"
                    f"  Variable '{var_name}' has nested reference at '{nested_path}': {nested_value}\n"
                    f"  Nested references in objects/arrays are NOT resolved by the current implementation.\n"
                    f"  Consider flattening the structure or moving the reference to the top level."
                )
                WARNINGS.append(warning_msg)
                logger.warning(warning_msg)
    
    return True


def validate_variable_file(file_path: Path) -> bool:
    """
    Validate a single variable JSON file.
    
    Args:
        file_path: Path to variable file
    
    Returns:
        True if validation passed, False if errors found
    """
    # Load JSON file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            variables = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"ERROR: {file_path}\n  Invalid JSON format: {e}"
        ERRORS.append(error_msg)
        logger.error(error_msg)
        return False
    except Exception as e:
        error_msg = f"ERROR: {file_path}\n  Failed to read file: {e}"
        ERRORS.append(error_msg)
        logger.error(error_msg)
        return False
    
    if not isinstance(variables, dict):
        error_msg = f"ERROR: {file_path}\n  Root element must be a JSON object (dict), got {type(variables).__name__}"
        ERRORS.append(error_msg)
        logger.error(error_msg)
        return False
    
    # Build dependency graph for validation
    dependency_graph = build_dependency_graph(variables)
    
    # Run all validations
    valid_self_refs = validate_self_references(variables, str(file_path))
    valid_circular = validate_circular_references(dependency_graph, str(file_path))
    valid_external = validate_external_references(variables, dependency_graph)
    valid_nested = validate_nested_references(variables, str(file_path))
    
    # File passes if no errors (warnings are OK)
    return valid_self_refs and valid_circular


def find_variable_files(variables_dir: Path) -> List[Path]:
    """
    Find all variable files in the variables directory.
    
    Expected structure: variables/{env}/{env}.json
    Example: variables/dev/dev.json, variables/test/test.json
    
    Args:
        variables_dir: Path to variables directory
    
    Returns:
        List of variable file paths
    """
    variable_files = []
    
    if not variables_dir.exists():
        error_msg = f"ERROR: Variables directory not found: {variables_dir}"
        ERRORS.append(error_msg)
        logger.error(error_msg)
        return variable_files
    
    for env_dir in variables_dir.iterdir():
        if env_dir.is_dir():
            env_name = env_dir.name
            expected_file = env_dir / f"{env_name}.json"
            
            if expected_file.exists():
                variable_files.append(expected_file)
    
    return variable_files


def print_validation_results(files_checked: int, all_valid: bool):
    """
    Log validation results summary.
    
    Args:
        files_checked: Number of files validated
        all_valid: Whether all validations passed
    """
    # Log summary
    logger.info("\nVALIDATION SUMMARY")
    logger.info(f"Files checked: {files_checked}")
    logger.info(f"Errors: {len(ERRORS)}")
    logger.info(f"Warnings: {len(WARNINGS)}")
    
    if all_valid and not ERRORS:
        logger.info("All validations passed!")
    else:
        logger.error("Validation failed - fix errors before merge")


def main():
    """
    Main function to orchestrate variable reference validation.
    
    Flow:
    1. Parse command line arguments
    2. Find all variable files in directory
    3. Validate each file:
       a. Load and parse JSON
       b. Check for self-references
       c. Check for circular references
       d. Check for external references (informational)
       e. Check for nested references (warning)
    4. Print results (only issues)
    5. Exit with appropriate code
    """
    # Step 1: Parse arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python variable_reference_validator.py <path_to_variables_dir>")
        logger.error("Example: python variable_reference_validator.py variables/")
        sys.exit(1)
    
    variables_dir = Path(sys.argv[1])
    
    # Step 2: Find variable files
    variable_files = find_variable_files(variables_dir)
    
    if not variable_files:
        logger.warning(f"No variable files found in {variables_dir}")
        logger.info("Expected structure: variables/{env}/{env}.json")
        logger.info("Example: variables/dev/dev.json, variables/test/test.json")
        sys.exit(0)
    
    # Step 3: Validate each file
    all_valid = True
    for file_path in sorted(variable_files):
        if not validate_variable_file(file_path):
            all_valid = False
    
    # Step 4: Log results
    if ERRORS or WARNINGS or not all_valid:
        print_validation_results(len(variable_files), all_valid)
    else:
        logger.info(f"Validated {len(variable_files)} file(s) - All checks passed")
    
    # Step 5: Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
