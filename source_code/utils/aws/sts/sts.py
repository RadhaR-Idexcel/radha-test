"""
AWS STS (Security Token Service) client for role assumption and temporary credentials.
"""
# Third party imports
import boto3
from botocore.config import Config

# Local imports
from logger_config import get_logger

# Local variable declarations
logger = get_logger(__name__)


class STSClient:
    """
    Shared client for AWS STS (Security Token Service) interactions.
    Handles role assumption and temporary credential management.
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
                 region_name=None):
        """
        Initializes the STSClient with optional AWS credentials.
        
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
                'sts',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=config
            )
            logger.debug('STS client initialized with provided credentials.')
        else:
            self.client = boto3.client('sts', config=config)
            logger.debug('STS client initialized with default credentials.')

    def assume_role(self, role_arn, session_name='AWSSession', duration_seconds=3600, policy=None, external_id=None):
        """
        Assume an IAM role and return temporary credentials.
        
        Args:
            role_arn (str): ARN of the role to assume.
            session_name (str): Session name for the assumed role. Defaults to 'AWSSession'.
            duration_seconds (int): Duration of the session in seconds. Defaults to 3600 (1 hour).
            policy (str, optional): IAM policy in JSON format to further restrict permissions. Defaults to None.
            external_id (str, optional): External ID for cross-account role assumption. Defaults to None.
        
        Returns:
            dict: Response from assume_role containing Credentials.
        
        Raises:
            Exception: If role assumption fails.
        """
        try:
            logger.debug('Assuming role: %s with session: %s', role_arn, session_name)
            
            kwargs = {
                'RoleArn': role_arn,
                'RoleSessionName': session_name[:64],
                'DurationSeconds': duration_seconds
            }
            
            if policy:
                kwargs['Policy'] = policy
                logger.debug('Applying inline session policy for least privilege access')
            
            if external_id:
                kwargs['ExternalId'] = external_id
                logger.debug('Using ExternalId for cross-account role assumption')
            
            response = self.client.assume_role(**kwargs)
            logger.info('Successfully assumed role: %s', role_arn)
            return response
        except Exception as e:
            logger.error('Failed to assume role %s: %s', role_arn, e)
            raise

    def get_caller_identity(self):
        """
        Get details about the current IAM identity.
        
        Returns:
            dict: Response containing Account, UserId, and Arn of the caller.
        """
        try:
            response = self.client.get_caller_identity()
            logger.debug('Caller identity: %s', response)
            return response
        except Exception as e:
            logger.error('Failed to get caller identity: %s', e)
            raise
