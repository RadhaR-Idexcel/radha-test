"""
This code contains s3 upload function
"""
# Standard imports
import hashlib
import base64

# Third party imports
import boto3
from botocore.exceptions import ClientError

# Local imports
from logger_config import logger

# Static variable declarations
API_MAX_RETRIES = 3


# Boto3 service wise client declarations
s3_client = boto3.client('s3')


def upload_file(source_file_path, bucket_name, key):
    """
    This function uploads the file to provided s3 bucket location using boto3 upload_file API.
    """
    try:
        s3_client.upload_file(source_file_path, bucket_name, key)
        logger.info('S3 Upload succeeded: s3\72\57\57%s/%s', bucket_name, key)
    except Exception as e:
        logger.error('An error occurred in upload_file: %s', e)
        raise e


def upload_bytes(data, bucket_name, key, upload_by, upload_date):
    """
    This function uploads the bytes to provided s3 bucket location using boto3 put_object API,
    with retry logic for "Content-MD5" errors.
    """
    for _ in range(API_MAX_RETRIES):
        try:
            data_md5 = base64.b64encode(hashlib.md5(data.encode('utf-8')).digest()).decode('utf-8')
            put_obj_res = s3_client.put_object(Body=data, Bucket=bucket_name,
                                               Key=key,
                                               Tagging=
                                               f'UploadBy={upload_by}&UploadDate={upload_date}',
                                               ContentMD5=data_md5)
            logger.info('S3 Upload succeeded: s3\72\57\57%s/%s', bucket_name, key)
            return put_obj_res
        except ClientError as e:
            if e.response['Error']['Code'] == 'BadDigest':
                logger.warning(
                    'The Content-MD5 you specified did not match what we received, Retrying...')
            else:
                raise e
        except Exception as e:
            logger.error('An error occurred in upload_bytes: %s', e)
            raise e
    raise e


def get_object(bucket_name, key):
    """ Downloading object from s3 using boto3 get_object API """
    try:
        get_obj_res = s3_client.get_object(Bucket=bucket_name, Key=key)
        logger.info('S3 download succeeded: s3\72\57\57%s/%s', bucket_name, key)
        return get_obj_res
    except Exception as e:
        logger.error('An error occurred in get_object: %s', e)
        raise e
