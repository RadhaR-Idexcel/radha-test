"""
Common code to check the input details before proceeding with the logic
"""

# Standard imports
import os

# Third party imports

# Local imports
from logger_config import logger

def validate_events(event, req_keys):
    """ Confirming that all essential information has been provided """
    try:
        missing_fields = [field for field in req_keys if field not in event]
        if missing_fields:
            raise ValueError(
                f'MissingRequiredFields: {",".join(missing_fields)} missing in the event. '
                f'Input validation failed.')

        logger.info('All required fields present in event. Input validation successful.')
        return True
    except Exception as e:
        logger.error('An error occurred in validate_inputs: %s', e)
        raise e


def validate_envs(req_envs):
    """
    Function to validate whether required variables are present or not
    :param req_envs: List of variable to validate
    :return: True if all the variables exist
    """
    try:
        # Validate environment variables
        missing_envs = []
        empty_values = []
        for var in req_envs:
            if var not in os.environ:
                missing_envs.append(var)
            if not os.environ[var]:
                empty_values.append(var)
        if missing_envs:
            logger.info('Missing required environment variable: %s', ",".join(missing_envs))
            raise ValueError(f'Missing required environment variable: {",".join(missing_envs)}')
        if empty_values:
            logger.info('Values are passed for following variables: %s', ",".join(empty_values))
        return True
    except Exception as e:
        logger.error('An error occurred in validate_envs: %s', e)
        raise e
