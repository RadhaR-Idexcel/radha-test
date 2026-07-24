"""
AWS ECR (Elastic Container Registry) client for repository management.
"""
# Third party imports
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Local imports
from logger_config import get_logger

# Local variable declarations
logger = get_logger(__name__)


class ECRClient:
    """
    Shared client for AWS ECR (Elastic Container Registry) interactions.
    Handles repository management and authentication.
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
                 region_name=None):
        """
        Initializes the ECRClient with optional AWS credentials.
        
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
                'ecr',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=config
            )
            logger.debug('ECR client initialized with provided credentials.')
        else:
            self.client = boto3.client('ecr', region_name=region_name, config=config)
            logger.debug('ECR client initialized with default credentials.')
        
        self.region_name = region_name or self.client.meta.region_name

    def describe_repositories(self, repository_names=None):
        """
        Describe ECR repositories.
        
        Args:
            repository_names (list, optional): List of repository names to describe.
        
        Returns:
            dict: Response containing repository descriptions.
        
        Raises:
            Exception: If describe operation fails.
        """
        try:
            if repository_names:
                logger.debug('Describing repositories: %s', repository_names)
                response = self.client.describe_repositories(repositoryNames=repository_names)
            else:
                logger.debug('Describing all repositories')
                response = self.client.describe_repositories()
            logger.info('Successfully described repositories.')
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryNotFoundException':
                logger.debug('Repository not found: %s', repository_names)
                return None
            else:
                logger.error('Failed to describe repositories: %s', e)
                raise
        except Exception as e:
            logger.error('Failed to describe repositories: %s', e)
            raise

    def create_repository(self, repository_name, image_tag_mutability='MUTABLE', 
                         scan_on_push=False, tags=None):
        """
        Create an ECR repository.
        
        Args:
            repository_name (str): Name of the repository to create.
            image_tag_mutability (str): Tag mutability setting. Defaults to 'MUTABLE'.
            scan_on_push (bool): Whether to scan images on push. Defaults to False.
            tags (list, optional): List of tags to apply to the repository. Each tag is a dict with 'Key' and 'Value'.
        
        Returns:
            dict: Response containing repository information.
        
        Raises:
            Exception: If creation fails.
        """
        try:
            logger.debug('Creating repository: %s', repository_name)
            
            # Build create_repository parameters
            create_params = {
                'repositoryName': repository_name,
                'imageTagMutability': image_tag_mutability,
                'imageScanningConfiguration': {'scanOnPush': scan_on_push}
            }
            
            # Add tags if provided
            if tags:
                create_params['tags'] = tags
                logger.debug('Adding tags to repository: %s', tags)
            
            response = self.client.create_repository(**create_params)
            logger.info('Successfully created repository: %s', repository_name)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryAlreadyExistsException':
                logger.warning('Repository already exists: %s', repository_name)
                # Return existing repository info
                return self.describe_repositories([repository_name])
            else:
                logger.error('Failed to create repository %s: %s', repository_name, e)
                raise
        except Exception as e:
            logger.error('Failed to create repository %s: %s', repository_name, e)
            raise

    def set_repository_policy(self, repository_name, policy_text):
        """
        Set the repository policy for an ECR repository.
        
        Args:
            repository_name (str): Name of the repository.
            policy_text (str): JSON policy document as a string.
        
        Returns:
            dict: Response containing policy information.
        
        Raises:
            Exception: If setting policy fails.
        """
        try:
            logger.debug('Setting repository policy for: %s', repository_name)
            response = self.client.set_repository_policy(
                repositoryName=repository_name,
                policyText=policy_text
            )
            logger.info('Successfully set repository policy for: %s', repository_name)
            return response
        except Exception as e:
            logger.error('Failed to set repository policy for %s: %s', repository_name, e)
            raise

    def put_lifecycle_policy(self, repository_name, lifecycle_policy_text):
        """
        Set the lifecycle policy for an ECR repository.
        
        Args:
            repository_name (str): Name of the repository.
            lifecycle_policy_text (str): JSON lifecycle policy document as a string.
        
        Returns:
            dict: Response containing lifecycle policy information.
        
        Raises:
            Exception: If setting lifecycle policy fails.
        """
        try:
            logger.debug('Setting lifecycle policy for: %s', repository_name)
            response = self.client.put_lifecycle_policy(
                repositoryName=repository_name,
                lifecyclePolicyText=lifecycle_policy_text
            )
            logger.info('Successfully set lifecycle policy for: %s', repository_name)
            return response
        except Exception as e:
            logger.error('Failed to set lifecycle policy for %s: %s', repository_name, e)
            raise

    def get_authorization_token(self):
        """
        Get authorization token for Docker login to ECR.
        
        Returns:
            dict: Response containing authorization data including token and endpoint.
        
        Raises:
            Exception: If token retrieval fails.
        """
        try:
            logger.debug('Getting ECR authorization token')
            response = self.client.get_authorization_token()
            logger.info('Successfully retrieved authorization token.')
            return response
        except Exception as e:
            logger.error('Failed to get authorization token: %s', e)
            raise
