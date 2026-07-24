"""
This code contains s3 upload function
"""
# Third party imports
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


# Local imports
from logger_config import get_logger

# Local variable declarations
logger= get_logger(__name__)
API_MAX_RETRIES = 3

class S3Client:
    """
    Shared client for AWS S3 interactions.
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
                 region_name=None):
        """
        Initializes the s3Client with optional AWS credentials.
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
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=config
            )
            logger.debug('S3 client initialized with provided credentials.')
        else:
            self.client = boto3.client('s3', config=config)
            logger.debug('S3 client initialized with default credentials.')


    def upload_file(self, source_file_path, bucket_name, key):
        """
        Uploading file to s3 using boto3 upload_file API
        Args:
            source_file_path (str): Local path of the file to be uploaded.
            bucket_name (str): Name of the S3 bucket.
            key (str): Key of the S3 object.
        Returns:
            None
        """
        try:
            self.client.upload_file(source_file_path, bucket_name, key)
            logger.info('S3 Upload succeeded: s3\72\57\57%s/%s', bucket_name, key)
        except Exception as e:
            logger.error('An error occurred in upload_file: %s', e)
            raise


    def upload_bytes(self, data, bucket_name, key, **args):
        """
        Uploading bytes data to s3 using boto3 put_object API
        Args:
            data (str | bytes): Data to be uploaded to S3.
            bucket_name (str): Name of the S3 bucket.
            key (str): Key of the S3 object.
            upload_by (str, optional): Identifier for who is uploading the object. Defaults to None.
            upload_date (str, optional): Date of upload. Defaults to None.
        Returns:
            dict: Response from S3 put_object API.
        """
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        for _ in range(API_MAX_RETRIES):
            try:
                arg = {
                    'Body': data_bytes,
                    'Bucket': bucket_name,
                    'Key': key,
                    **args
                }

                put_obj_res = self.client.put_object(**arg)
                return put_obj_res
            except ClientError as e:
                logger.warning('ClientError occurred in upload_bytes: %s', e)
                raise
            except Exception as e:
                logger.error('An error occurred in upload_bytes: %s', e)
                raise
        raise RuntimeError(f'Max retries exceeded for upload_bytes to s3. '
                           f's3\72\57\57{bucket_name}/{key}')


    def get_object(self, bucket_name, key):
        """
        Getting object from s3 using boto3 get_object API

        Args:
            bucket_name (str): Name of the S3 bucket.
            key (str): Key of the S3 object.        
        Returns:
            dict: Response from S3 get_object API.
        """
        try:
            get_obj_res = self.client.get_object(Bucket=bucket_name, Key=key)
            logger.info('S3 download succeeded: s3\72\57\57%s/%s', bucket_name, key)
            return get_obj_res
        except ClientError as ce:
            if ce.response['Error']['Code'] == 'NoSuchKey':
                logger.warning('The object s3\72\57\57%s/%s does not exist.', bucket_name, key)
                raise
            else:
                # Re-raise other ClientErrors (AccessDenied, etc.)
                logger.error('ClientError occurred in get_object: %s', ce)
                raise
        except Exception as e:
            logger.error('An error occurred in get_object: %s', e)
            raise

    def download_file(self, bucket_name, key, download_path):
        """
        Downloading file from s3 using boto3 download_file API

        Args:
            bucket_name (str): Name of the S3 bucket.
            key (str): Key of the S3 object.
            download_path (str): Local path to save the downloaded file.

        Returns:
            None
        """
        try:
            self.client.download_file(bucket_name, key, download_path)
            logger.info('S3 download succeeded: s3\72\57\57%s/%s to %s', bucket_name,
                        key, download_path)
        except Exception as e:
            logger.error('An error occurred in download_file: %s', e)
            raise

    def head_bucket(self, bucket_name):
        """
        Check if an S3 bucket exists and is accessible.

        Args:
            bucket_name (str): Name of the S3 bucket.

        Returns:
            dict: Response from head_bucket API.

        Raises:
            ClientError: If bucket doesn't exist or permission denied
            Exception: For other errors
        """
        try:
            response = self.client.head_bucket(Bucket=bucket_name)
            logger.debug('Bucket exists and is accessible: s3\72\57\57%s', bucket_name)
            return response
        except ClientError as ce:
            error_code = ce.response.get('Error', {}).get('Code', 'Unknown')
            if error_code in ('404', 'NoSuchBucket'):
                logger.warning('Bucket does not exist: s3\72\57\57%s', bucket_name)
            elif error_code == '403':
                logger.warning('Access denied to bucket: s3\72\57\57%s', bucket_name)
            else:
                logger.error('ClientError in head_bucket for s3\72\57\57%s: %s',
                           bucket_name, ce)
            raise
        except Exception as e:
            logger.error('An error occurred in head_bucket: %s', e)
            raise

    def head_object(self, bucket_name, key):
        """
        Retrieve metadata of an object without downloading it.

        Args:
            bucket_name (str): Name of the S3 bucket.
            key (str): Key of the S3 object.

        Returns:
            dict: Response from head_object API containing object metadata.
            
        Raises:
            ClientError: If object doesn't exist (404) or permission denied
            Exception: For other errors
        """
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=key)
            logger.debug('Retrieved metadata for s3\72\57\57%s/%s', bucket_name, key)
            return response
        except ClientError as ce:
            error_code = ce.response.get('Error', {}).get('Code', 'Unknown')
            if error_code in ('404', 'NoSuchKey'):
                logger.warning('Object does not exist: s3\72\57\57%s/%s', bucket_name, key)
            else:
                logger.error('ClientError in head_object for s3\72\57\57%s/%s: %s', 
                           bucket_name, key, ce)
            raise
        except Exception as e:
            logger.error('An error occurred in head_object: %s', e)
            raise

    def get_object_tagging(self, bucket_name, key):
        """
        Get tags for an S3 object.

        Args:
            bucket_name (str): Name of the S3 bucket.
            key (str): Key of the S3 object.

        Returns:
            dict: Response from get_object_tagging API containing TagSet.
            
        Raises:
            ClientError: If object doesn't exist or permission denied
            Exception: For other errors
        """
        try:
            response = self.client.get_object_tagging(Bucket=bucket_name, Key=key)
            logger.debug('Retrieved tags for s3\72\57\57%s/%s', bucket_name, key)
            return response
        except ClientError as ce:
            error_code = ce.response.get('Error', {}).get('Code', 'Unknown')
            if error_code in ('404', 'NoSuchKey'):
                logger.debug('Object does not exist (no tags): s3\72\57\57%s/%s', bucket_name, key)
            else:
                logger.warning('ClientError in get_object_tagging for s3\72\57\57%s/%s: %s', 
                             bucket_name, key, ce)
            raise
        except Exception as e:
            logger.error('An error occurred in get_object_tagging: %s', e)
            raise

    def list_files(self, bucket_name, prefix, suffix=''):
        """
        List all files in S3 bucket with given prefix and optional suffix filter.
        Returns sorted list of matching file keys.

        Args:
            bucket_name (str): Name of the S3 bucket.
            prefix (str): Prefix path to filter objects.
            suffix (str, optional): File extension or suffix to filter (e.g., '.json'). Defaults to ''.
        Returns:
            list: Sorted list of S3 object keys matching the criteria.
        """
        try:
            matching_files = []
            paginator = self.client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Filter by suffix if provided
                        if not suffix or key.endswith(suffix):
                            matching_files.append(key)

            # Sort alphabetically
            matching_files.sort()
            return matching_files

        except Exception as e:
            logger.error('An error occurred in list_files: %s', e)
            raise
