"""
Function to check the basic input details before proceeding with the logic
"""

# Standard imports

# Third party imports
import boto3

# Local imports
from logger_config import logger

cognito_clt = boto3.client('cognito-idp')

def list_user_pools():
    """
    Function to list all the existing user pools in environment as part of off boarding evidence.
    :return: User pool details in dictionary format.
    """
    try:
        user_pool_details = []
        # Get the paginator for the 'list_user_pools' operation
        paginator = cognito_clt.get_paginator('list_user_pools')

        # Define the pagination operation with the required parameters
        page_iterator = paginator.paginate(MaxResults=50)  # MaxResults can be adjusted as needed

        # Iterate through each page of results
        for page in page_iterator:
            user_pools = page['UserPools']
            for pool in user_pools:
                pool_id = pool['Id']
                pool_name = pool['Name']
                logger.debug("User Pool ID: %s, Name: %s", pool_id, pool_name)
                user_pool_details.append({'UserPoolId': pool_id, 'UserPoolName': pool_name})
        return user_pool_details
    except Exception as e:
        logger.info('An error occurred in update_user_pool_deletion_protection: %s', e)
        raise e


def update_user_pool_deletion_protection(user_pool_ids):
    """Update DeletionProtection to INACTIVE for each Cognito User Pool in the list."""
    try:
        for user_pool_id in user_pool_ids:
            logger.info('Updating DeletionProtection to INACTIVE for User Pool: %s', user_pool_id)
            cognito_clt.update_user_pool(UserPoolId=user_pool_id, DeletionProtection='INACTIVE')
            logger.info('Successfully updated DeletionProtection for User Pool: %s', user_pool_id)
    except Exception as e:
        logger.error('An error occurred in update_user_pool_deletion_protection: %s', e)
        raise e
