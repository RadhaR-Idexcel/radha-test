"""
Utility wrapper for AWS CloudWatch Logs interactions.
Provides log group discovery, Insights query execution, and result retrieval.
"""
# Standard library imports
import time

# Third-party imports
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Local imports
from logger_config import get_logger

logger = get_logger(__name__)

_CWL_CONFIG = Config(retries={"max_attempts": 3, "mode": "standard"})


class CloudWatchLogsClient:
    """
    Shared client for AWS CloudWatch Logs interactions.
    Uses IAM role credentials by default (Lambda execution role).
    """

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 aws_session_token=None, region_name=None):
        """
        Initialises the CloudWatch Logs boto3 client.
        :param aws_access_key_id: AWS access key ID (optional).
        :param aws_secret_access_key: AWS secret access key (optional).
        :param aws_session_token: AWS session token (optional).
        :param region_name: AWS region name. Defaults to the Lambda runtime region.
        """
        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client(
                "logs",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                config=_CWL_CONFIG,
            )
            logger.debug("CloudWatch Logs client initialised with provided credentials.")
        else:
            self.client = boto3.client(
                "logs",
                region_name=region_name,
                config=_CWL_CONFIG,
            )
            logger.debug("CloudWatch Logs client initialised with default credentials.")

    # ── Log group discovery ───────────────────────────────────────────────────

    def list_log_groups(self, prefix=None):
        """
        Returns a list of all log group names, optionally filtered by prefix.
        Handles pagination transparently.
        :param prefix: Optional log group name prefix to filter by.
        :return: list[str] of log group names.
        """
        try:
            kwargs = {}
            if prefix:
                kwargs["logGroupNamePrefix"] = prefix

            groups = []
            paginator = self.client.get_paginator("describe_log_groups")
            for page in paginator.paginate(**kwargs):
                for group in page.get("logGroups", []):
                    groups.append(group["logGroupName"])

            logger.debug("Found %d log group(s) with prefix '%s'", len(groups), prefix)
            return groups

        except ClientError as e:
            logger.error("ClientError in list_log_groups: %s", e)
            raise
        except Exception as e:
            logger.error("An error occurred in list_log_groups: %s", e)
            raise

    # ── Insights query ────────────────────────────────────────────────────────

    def start_query(self, log_group_names, start_time_sec, end_time_sec, query_string):
        """
        Starts a CloudWatch Logs Insights query across a list of log groups.
        :param log_group_names: list[str] of log group names to query.
        :param start_time_sec: Query start time as Unix epoch seconds (int).
        :param end_time_sec: Query end time as Unix epoch seconds (int).
        :param query_string: CloudWatch Logs Insights query string.
        :return: queryId string.
        """
        try:
            resp = self.client.start_query(
                logGroupNames=log_group_names,
                startTime=int(start_time_sec),
                endTime=int(end_time_sec),
                queryString=query_string,
                limit=10000,
            )
            query_id = resp["queryId"]
            logger.info(
                "Started Insights query '%s' across %d group(s): queryId=%s",
                query_string[:60],
                len(log_group_names),
                query_id,
            )
            return query_id

        except ClientError as e:
            logger.error("ClientError in start_query: %s", e)
            raise
        except Exception as e:
            logger.error("An error occurred in start_query: %s", e)
            raise

    def get_query_results(self, query_id):
        """
        Fetches the current status and results of a CloudWatch Logs Insights query.
        :param query_id: Query ID returned by start_query().
        :return: dict with keys:
                   status  – one of 'Scheduled'|'Running'|'Complete'|'Failed'|'Cancelled'|'Timeout'
                   results – list of result row dicts {field: value} (may be empty if not complete)
                   stats   – query statistics dict from AWS (may be absent)
        """
        try:
            resp = self.client.get_query_results(queryId=query_id)
            status = resp.get("status", "Unknown")
            raw_rows = resp.get("results", [])

            # Convert AWS field/value pair format → plain dicts.
            results = []
            for row in raw_rows:
                row_dict = {item["field"]: item["value"] for item in row}
                results.append(row_dict)

            logger.debug(
                "Query %s status=%s rows=%d", query_id, status, len(results)
            )
            return {
                "status": status,
                "results": results,
                "stats": resp.get("statistics", {}),
            }

        except ClientError as e:
            logger.error("ClientError in get_query_results: %s", e)
            raise
        except Exception as e:
            logger.error("An error occurred in get_query_results: %s", e)
            raise

    def stop_query(self, query_id):
        """
        Cancels a running CloudWatch Logs Insights query.
        :param query_id: Query ID to cancel.
        :return: True if the query was stopped, False if already finished.
        """
        try:
            resp = self.client.stop_query(queryId=query_id)
            stopped = resp.get("success", False)
            logger.info("stop_query %s → success=%s", query_id, stopped)
            return stopped
        except ClientError as e:
            logger.error("ClientError in stop_query: %s", e)
            raise
        except Exception as e:
            logger.error("An error occurred in stop_query: %s", e)
            raise

    def wait_for_query(self, query_id, poll_interval_sec=2, max_wait_sec=60):
        """
        Blocks until the query reaches a terminal state (Complete / Failed / Cancelled / Timeout).
        :param query_id: Query ID to wait on.
        :param poll_interval_sec: Seconds between polls (default 2).
        :param max_wait_sec: Maximum seconds to wait before raising TimeoutError (default 60).
        :return: Final get_query_results() response dict.
        :raises TimeoutError: if max_wait_sec is exceeded without reaching a terminal state.
        """
        terminal = {"Complete", "Failed", "Cancelled", "Timeout"}
        waited = 0
        while waited < max_wait_sec:
            result = self.get_query_results(query_id)
            if result["status"] in terminal:
                return result
            time.sleep(poll_interval_sec)
            waited += poll_interval_sec
        raise TimeoutError(
            f"Query {query_id} did not complete within {max_wait_sec}s"
        )
