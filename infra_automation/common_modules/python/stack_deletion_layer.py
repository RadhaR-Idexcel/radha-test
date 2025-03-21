"""
This module contains functions for describing CloudFormation stacks and deleting stacks.
"""
import boto3
import botocore
from logger_config import logger

# Initialize AWS clients
cft_client = boto3.client('cloudformation')


def describe_stack(stack_name):
    """Retrieve details and resources for the specified CF Stk or raise exception if not found."""
    try:
        # Fetch stack details to confirm existence
        stack_info = cft_client.describe_stacks(StackName=stack_name)
        stack_details = stack_info['Stacks'][0]

        # Fetch resources for the stack
        resources = cft_client.describe_stack_resources(StackName=stack_name)['StackResources']
        resource_types = [resource['ResourceType'] for resource in resources]

        return {
            'StackDetails': stack_details,
            'StackResources': resources,
            'ResourceTypes': resource_types
        }

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            logger.warning('Stack not found(%s).', stack_name)
            return False
        logger.error("An client error occurred in describe_stack: %s", e)
        raise e
    except Exception as e:
        logger.error("An error occurred in describe_stack: %s", e)
        raise e


def delete_stack(stack_name):
    """Delete the CloudFormation stack."""
    try:
        logger.info("Initiating deletion of stack: %s", stack_name)
        cft_client.delete_stack(StackName=stack_name)
        waiter = cft_client.get_waiter('stack_delete_complete')
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 10
            }
        )
        logger.info("Stack %s has been deleted successfully", stack_name)
    except botocore.exceptions.ClientError as e:
        logger.error("An client error occurred in delete_stack: %s", e)
        raise e
    except Exception as e:
        logger.error("An error occurred in delete_stack: %s", e)
        raise e


def get_stack_outputs(stack_name):
    """
    This function retrieves and delivers CloudFormation stack outputs.
    """
    try:
        stk_outputs = {}
        stk_res = cft_client.describe_stacks(StackName=stack_name)
        if 'Outputs' in stk_res['Stacks'][0]:
            for item in stk_res['Stacks'][0]['Outputs']:
                key = item['OutputKey']
                value = item['OutputValue']
                stk_outputs[key] = value
        if len(stk_outputs) != 0:
            return stk_outputs

        return {}
    except Exception as e:
        logger.error("An error occurred in get_stack_outputs: %s", e)
        raise e
