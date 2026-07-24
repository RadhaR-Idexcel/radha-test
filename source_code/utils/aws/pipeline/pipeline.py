"""
Pipeline class for interacting with AWS CodePipeline API's.
"""

# Third party imports
import boto3
from botocore.config import Config

# Local imports
from logger_config import get_logger

# Local variable declarations
logger= get_logger(__name__)

class PipelineClient:
    """
    Shared client for AWS CodePipeline interactions.
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
                 region_name=None):
        """
        Initializes the PipelineClient with optional AWS credentials.
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
                'codepipeline',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=config
            )
            logger.debug('Codepipeline client initialized with provided credentials.')
        else:
            self.client = boto3.client('codepipeline', config=config)
            logger.debug('Codepipeline client initialized with default credentials.')

    def put_job_success_result(self, job_id, continuation_token=None, **args):
        """
        Put job success result to AWS CodePipeline.

        Args:
            job_id (str): The ID of the job.
            **args: Additional keyword arguments to pass to the API. Supported keys include:
                - continuationToken (str, optional): Continuation token for the job.

        Returns:
            None
        """
        api_args = {
            'jobId': job_id,
            **args
        }
        if continuation_token:
            api_args['continuationToken'] = continuation_token
            
        self.client.put_job_success_result(
            **api_args
        )
        logger.info('Reported job success for pipeline job ID: %s', job_id)


    def put_job_failure_result(self, job_id, job_type, message):
        """
        Put job failure result to AWS CodePipeline.

        Args:
            job_id (str): The ID of the job.
            job_type (str): The type of the job failure.
            message (str): The failure message.

        Returns: None
        """
        api_args = {
                'jobId': job_id,
                'failureDetails': {
                    'type': job_type,
                    'message': message
                }
            }
        self.client.put_job_failure_result(**api_args)
        logger.info('Reported job failure for pipeline job ID: %s', job_id)
