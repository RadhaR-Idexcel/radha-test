"""
AWS SSM (Systems Manager) Parameter Store client.
"""
# Third party imports
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Local imports
from logger_config import get_logger

# Local variable declarations
logger = get_logger(__name__)


class SSMClient:
    """
    Shared client for AWS SSM (Systems Manager) Parameter Store interactions.
    Handles parameter storage and retrieval.
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
                 region_name=None):
        """
        Initializes the SSMClient with optional AWS credentials.
        
        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access key. Defaults to None.
            aws_session_token (str, optional): AWS session token. Defaults to None.
            region_name (str, optional): AWS region name. Defaults to None.
        
        Returns:
            None
        """
        config = Config(retries={'max_attempts': 3, 'mode': 'standard'})

        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client(
                'ssm',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=config
            )
            logger.debug('SSM client initialized with provided credentials.')
        else:
            self.client = boto3.client('ssm', region_name=region_name, config=config)
            logger.debug('SSM client initialized with default credentials.')

    def put_parameter(self, name, value, parameter_type='String', overwrite=True, 
                     description=None):
        """
        Put a parameter in SSM Parameter Store.
        
        Args:
            name (str): Name of the parameter.
            value (str): Value of the parameter.
            parameter_type (str): Type of parameter ('String', 'StringList', 'SecureString').
            overwrite (bool): Whether to overwrite existing parameter. Defaults to True.
            description (str, optional): Description of the parameter.
        
        Returns:
            dict: Response from put_parameter operation.
        
        Raises:
            Exception: If put operation fails.
        """
        try:
            logger.debug('Putting parameter: %s', name)
            kwargs = {
                'Name': name,
                'Value': value,
                'Type': parameter_type,
                'Overwrite': overwrite
            }
            
            if description:
                kwargs['Description'] = description
            
            response = self.client.put_parameter(**kwargs)
            logger.info('Successfully put parameter: %s', name)
            return response
        except Exception as e:
            logger.error('Failed to put parameter %s: %s', name, e)
            raise

    def get_parameter(self, name, with_decryption=True):
        """
        Get a parameter from SSM Parameter Store.
        
        Args:
            name (str): Name of the parameter to retrieve.
            with_decryption (bool): Whether to decrypt SecureString parameters. Defaults to True.
        
        Returns:
            dict: Response containing parameter information.
        
        Raises:
            Exception: If get operation fails.
        """
        try:
            logger.debug('Getting parameter: %s', name)
            response = self.client.get_parameter(
                Name=name,
                WithDecryption=with_decryption
            )
            logger.info('Successfully retrieved parameter: %s', name)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.debug('Parameter not found: %s', name)
                return None
            else:
                logger.error('Failed to get parameter %s: %s', name, e)
                raise
        except Exception as e:
            logger.error('Failed to get parameter %s: %s', name, e)
            raise

    def delete_parameter(self, name):
        """
        Delete a parameter from SSM Parameter Store.
        
        Args:
            name (str): Name of the parameter to delete.
        
        Returns:
            dict: Response from delete operation.
        
        Raises:
            Exception: If delete operation fails.
        """
        try:
            logger.debug('Deleting parameter: %s', name)
            response = self.client.delete_parameter(Name=name)
            logger.info('Successfully deleted parameter: %s', name)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning('Parameter not found for deletion: %s', name)
                return None
            else:
                logger.error('Failed to delete parameter %s: %s', name, e)
                raise
        except Exception as e:
            logger.error('Failed to delete parameter %s: %s', name, e)
            raise
