# custom-rules/check_single_s3.py

from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.cloudformation.checks.resource.base_resource_check import BaseResourceCheck

class SingleS3BucketPerStack(BaseResourceCheck):

    def __init__(self):
        name = "Ensure only one S3 bucket exists per stack"
        id = "CKV2_CUSTOM_1"
        supported_resources = ["AWS::S3::Bucket"]
        categories = [CheckCategories.GENERAL_SECURITY]
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_resources=supported_resources
        )
        self._bucket_count = {}             # tracks count per template file

    def scan_resource_conf(self, conf, **kwargs):
        file_path = kwargs.get("file_path", "default")

        # increment count for this stack
        self._bucket_count[file_path] = self._bucket_count.get(file_path, 0) + 1

        # first bucket passes, any additional bucket fails
        if self._bucket_count[file_path] > 1:
            return CheckResult.FAILED

        return CheckResult.PASSED

scanner = SingleS3BucketPerStack()