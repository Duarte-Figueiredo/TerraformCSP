from typing import Optional, Type

from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource


class AwsLambdaEventSourceMapping(TerraformResource):
    event_source_arn: Optional[str] = None
    topic: Optional[list[str]] = None
    queues: Optional[list[str]] = None

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_LAMBDA_EVENT_SOURCE_MAPPING

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers)

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        return super().get_references(references | {self.topic, self.queues, self.event_source_arn, self.name})


ALL_TERRAFORM_EVENTS: dict[str, Type[TerraformResource]] = {
    AwsLambdaEventSourceMapping.get_cloud_resource_type().value: AwsLambdaEventSourceMapping}
