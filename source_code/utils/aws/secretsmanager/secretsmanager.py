"""
This code contains AWS Secrets Manager utility functions
"""
# Third party imports
import boto3
import json
from botocore.config import Config
from botocore.exceptions import ClientError

# Local imports
from logger_config import get_logger

# Local variable declarations
logger = get_logger(__name__)
API_MAX_RETRIES = 3


class SecretsManagerClient:
    """
    Shared client for AWS Secrets Manager interactions.
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
                 region_name=None):
        """
        Initializes the SecretsManagerClient with optional AWS credentials.
        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access key. Defaults to None.
            aws_session_token (str, optional): AWS session token. Defaults to None.
            region_name (str, optional): AWS region name. Defaults to None.
        
        Returns:
            None
        """
        config = Config(retries={'max_attempts': API_MAX_RETRIES, 'mode': 'standard'})

        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client(
                'secretsmanager',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=config
            )
            logger.debug('Secrets Manager client initialized with provided credentials.')
        else:
            self.client = boto3.client('secretsmanager', config=config)
            logger.debug('Secrets Manager client initialized with default credentials.')

    def get_secret_value(self, secret_name: str) -> dict:
        """
        Retrieves a secret value from AWS Secrets Manager.
        
        Args:
            secret_name (str): The name or ARN of the secret to retrieve
        
        Returns:
            dict: The secret value as a dictionary (parsed JSON) or {'SecretString': value} if not JSON
        
        Raises:
            ClientError: If the secret cannot be retrieved
            ValueError: If the secret doesn't contain SecretString
        """
        try:
            logger.info(f"Retrieving secret: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                secret_string = response['SecretString']
                
                # Try to parse as JSON
                try:
                    secret_dict = json.loads(secret_string)
                    logger.debug(f"Secret {secret_name} retrieved and parsed as JSON")
                    return secret_dict
                except json.JSONDecodeError:
                    # If not JSON, return as plain string in a dict
                    logger.debug(f"Secret {secret_name} retrieved as plain string")
                    return {'SecretString': secret_string}
            else:
                error_msg = f"Secret {secret_name} does not contain SecretString"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = f"Failed to retrieve secret {secret_name}: {error_code} - {e.response['Error']['Message']}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error retrieving secret {secret_name}: {str(e)}"
            logger.error(error_msg)
            raise

    def get_secret_string(self, secret_name: str) -> str:
        """
        Retrieves a secret value as a string from AWS Secrets Manager.
        
        Args:
            secret_name (str): The name or ARN of the secret to retrieve
        
        Returns:
            str: The secret value as a string (unparsed)
        
        Raises:
            ClientError: If the secret cannot be retrieved
            ValueError: If the secret doesn't contain SecretString
        """
        try:
            logger.info(f"Retrieving secret string: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                logger.debug(f"Secret {secret_name} retrieved as string")
                return response['SecretString']
            else:
                error_msg = f"Secret {secret_name} does not contain SecretString"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = f"Failed to retrieve secret {secret_name}: {error_code} - {e.response['Error']['Message']}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error retrieving secret {secret_name}: {str(e)}"
            logger.error(error_msg)
            raise
