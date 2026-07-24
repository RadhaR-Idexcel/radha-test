"""
AWS boto3 CloudFormation shared functions are declared in this module to reuse
across different code bases.
"""
# Third party imports
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError


# Local imports
from logger_config import get_logger

# Local variable declarations
logger= get_logger(__name__)

class CloudFormationClient:
    """
    Shared client for AWS CloudFormation interactions.
    Supports dual-role operation:
    - Assumes d_role_arn for describe and validation operations
    - Uses d_cf_role_arn as CloudFormation service role in change set execution
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
                 region_name=None):
        """
        Initializes the CloudFormationClient with optional AWS credentials.
        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access key. Defaults to None.
            aws_session_token (str, optional): AWS session token. Defaults to None.
            region_name (str, optional): AWS region name. Defaults to None.
        
        Returns:
            None
        """
        config = Config(retries={'max_attempts': 3,'mode': 'standard'})


        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client(
                'cloudformation',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=config
            )
            logger.debug('CloudFormation client initialized with provided credentials.')
        else:
            self.client = boto3.client('cloudformation', config=config)
            logger.debug('CloudFormation client initialized with default credentials.')


    def describe_stack(self, stk_name):
        """
        Describe the CloudFormation stack with the given name.
        
        Args:
            stk_name (str): Name of the CloudFormation stack.
            
        Returns:
            dict: Response from describe_stacks API.
        """
        try:
            response = self.client.describe_stacks(StackName=stk_name)
            return response
        except Exception as e:
            logger.warning('An error occurred while describing stack: %s', e)
            raise


    def create_change_set(self, api_args):
        """
        Create a change set for the given stack.
        Automatically determines if this is a CREATE or UPDATE change set.
        
        Args:
            api_args (dict): Arguments for creating the change set.
                Must include 'StackName' and 'RoleARN' (CloudFormation service role).
            
        Returns:
            dict: Response from create_change_set API.
        """
        try:
            stk_name = api_args.get('StackName')
            api_args['ChangeSetType'] = 'UPDATE'
            try:
                # Check if stack exists
                self.describe_stack(stk_name)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ValidationError':
                    api_args['ChangeSetType'] = 'CREATE'
                else:
                    logger.error('An error occurred while checking stack existence: %s', e)
                    raise
            # Create change set (RoleARN in api_args handles permissions)
            response = self.client.create_change_set(**api_args)
            return response
        except Exception as e:
            logger.error('An error occurred while creating change set: %s', e)
            raise

    def change_set_create_wait(self, stk_name, cs_name):
        """
        Wait for the change set to be created.  
        Args:
            stk_name (str): Name of the CloudFormation stack.
            cs_name (str): Name of the change set.
        Returns:
            None    
        """
        try:
            waiter = self.client.get_waiter('change_set_create_complete')
            waiter.wait(
                StackName=stk_name,
                ChangeSetName=cs_name,
                WaiterConfig={
                    'Delay': 10,
                    'MaxAttempts': 89
                }
            )
        except WaiterError as e:
            logger.warning('An error occurred while waiting for change set creation: %s', e)
            raise

    def execute_change_set(self,stk_name, cs_name):
        """
        Execute the given change set for the specified stack.
        Args:
            stk_name (str): Name of the CloudFormation stack.
            cs_name (str): Name of the change set.
        Returns:
            None
        """
        try:
            response = self.client.execute_change_set(
                StackName=stk_name,
                ChangeSetName=cs_name
            )
            return response
        except ClientError as e:
            logger.error('An error occurred while executing change set: %s', e)
            raise

    def execute_change_set_wait(self, stk_name):
        """
        Wait for the stack update to complete after executing the change set.
        Args:
            stk_name (str): Name of the CloudFormation stack.
        Returns:
            None
        """
        try:
            waiter = self.client.get_waiter('stack_update_complete')
            waiter.wait(
                StackName=stk_name,
                WaiterConfig={
                    'Delay': 10,
                    'MaxAttempts': 89
                }
            )
        except ClientError as e:
            logger.error('An error occurred while waiting for stack update: %s', e)
            raise

    def stack_create_complete_wait(self, stk_name):
        """
        Wait for the stack creation to complete.
        Args:
            stk_name (str): Name of the CloudFormation stack.
        Returns:
            None
        """
        try:
            waiter = self.client.get_waiter('stack_create_complete')
            waiter.wait(
                StackName=stk_name,
                WaiterConfig={
                    'Delay': 10,
                    'MaxAttempts': 90
                }
            )
        except ClientError as e:
            logger.error('An error occurred while waiting for stack creation: %s', e)
            raise

    def describe_change_set(self, stk_name, cs_name):
        """
        Describe the change set to check if there are any changes.
        Args:
            stk_name (str): Name of the CloudFormation stack.
            cs_name (str): Name of the change set.
        Returns:
            dict: Response from describe_change_set API.
        """
        try:
            response = self.client.describe_change_set(
                StackName=stk_name,
                ChangeSetName=cs_name
            )
            return response
        except Exception as e:
            logger.error('An error occurred while describing change set: %s', e)
            raise

    def set_stack_policy(self, stk_name, stack_policy):
        """
        Set the stack policy for the given stack.
        Args:
            stk_name (str): Name of the CloudFormation stack.
            stack_policy (str): Stack policy document as JSON string.
        Returns:
            dict: Response from set_stack_policy API.
        """
        try:
            response = self.client.set_stack_policy(
                StackName=stk_name,
                StackPolicyBody=stack_policy
            )
            logger.info('Stack policy set for stack: %s', stk_name)
            return response
        except Exception as e:
            logger.error('An error occurred while setting stack policy: %s', e)
            raise
