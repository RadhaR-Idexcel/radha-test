"""
Jinja2 template rendering utilities with strict variable validation.
Uses ${variable} delimiter format for CloudFormation-style variable replacement.
"""
# Third party imports
from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError, meta

# Local imports
from logger_config import get_logger

# Local variable declarations
logger = get_logger(__name__)

# Shared Jinja2 Environment configuration
# NOSONAR: autoescape=False is required here - this utility renders CloudFormation
# infrastructure configs (ARNs, policies, resource names), not HTML content.
# Auto-escaping would corrupt AWS identifiers. No XSS risk in infrastructure code.
JINJA_ENV_CONFIG = {
    'variable_start_string': '${',
    'variable_end_string': '}',
    'autoescape': False
}


def render_string(template_string, variables):
    """
    Render a Jinja2 template string with variables using ${} delimiter syntax.
    
    Uses StrictUndefined to ensure all variables are defined - missing variables
    will raise an exception rather than rendering as empty strings.
    
    Args:
        template_string (str): Template string with ${Variable} placeholders.
        variables (dict): Dictionary of variable key-value pairs for substitution.
    
    Returns:
        str: Rendered string with all variables replaced.
    
    Raises:
        UndefinedError: If any variable in the template is not defined in variables dict.
        TemplateSyntaxError: If the template syntax is invalid.
    
    Example:
        >>> variables = {'Environment': 'Prod', 'Project': 'MyApp'}
        >>> template = 'Deploy ${Project} to ${Environment}'
        >>> render_string(template, variables)
        'Deploy MyApp to Prod'
    """
    try:
        # Create Jinja2 environment with custom delimiters and strict undefined
        env = Environment(**JINJA_ENV_CONFIG, undefined=StrictUndefined)
        
        # Compile and render template
        template = env.from_string(template_string)
        rendered = template.render(variables)
        
        logger.debug('Successfully rendered template with %d variables', len(variables))
        return rendered
        
    except UndefinedError as e:
        logger.warning('Missing variable in template: %s', str(e))
        raise ValueError(f'Template rendering failed - undefined variable: {str(e)}') from e
    except TemplateSyntaxError as e:
        logger.error('Invalid template syntax: %s', str(e))
        raise ValueError(f'Template rendering failed - syntax error: {str(e)}') from e


def find_undeclared_variables(template_string):
    """
    Find all undeclared variables in a Jinja2 template string.
    
    Uses Jinja2's meta module to parse the template AST and extract all
    variable names without rendering the template.
    
    Args:
        template_string (str): Template string with ${Variable} placeholders.
    
    Returns:
        set: Set of variable names used in the template.
    
    Example:
        >>> template = 'Deploy ${Project} to ${Environment}'
        >>> find_undeclared_variables(template)
        {'Project', 'Environment'}
    """
    try:
        # Create Jinja2 environment for AST parsing
        env = Environment(**JINJA_ENV_CONFIG)
        
        # Parse template to AST
        ast = env.parse(template_string)
        
        # Extract undeclared variable names
        variables = meta.find_undeclared_variables(ast)
        
        logger.debug('Found %d undeclared variables in template', len(variables))
        return variables
        
    except TemplateSyntaxError as e:
        logger.error('Invalid template syntax: %s', str(e))
        raise ValueError(f'Template parsing failed - syntax error: {str(e)}') from e
    except Exception as e:
        logger.error('Error rendering template: %s', str(e))
        raise
