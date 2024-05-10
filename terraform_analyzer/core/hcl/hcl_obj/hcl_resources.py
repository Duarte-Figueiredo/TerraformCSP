from typing import Type, Union, Optional

from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource

DEFAULT = "default"
METADATA = "metadata"
TAGS = "tags"
NAME = "name"
ENVIRONMENT = "environment"
VARIABLES = "variables"
DESCRIPTION = "description"


class TerraformComputeResource(TerraformResource):
    pass


class AwsLambda(TerraformComputeResource):
    role: Optional[str] = None
    environment: Optional[Union[dict, list]] = None
    env_variables: dict[str, str] = {}

    def model_post_init(self, __context):
        # TODO handle variables as str reference instead of dict block eg: "{'variables': '${var.lambda_runtime_environment_variables}'}"
        if type(self.environment) is dict:
            if VARIABLES in self.environment and type(self.environment[VARIABLES]) is dict:
                self.env_variables.update(self.environment[VARIABLES])
        elif type(self.environment) is list:
            for item in self.environment:
                if VARIABLES in item and type(item[VARIABLES]) is dict:
                    self.env_variables.update(item[VARIABLES])

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers)

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        str_env_variables: set[str] = set(
            filter(lambda x: type(x) is str, self.env_variables.values())) if self.env_variables else set()
        return super().get_references(references | str_env_variables | {self.role})

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_LAMBDA

    class Config:
        arbitrary_types_allowed = True


class AwsCluster(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_CLUSTER


class AwsInstance(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_INSTANCE


class GCloudFunction(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.GCLOUD_FUNCTION


class GCloudVmWareCluster(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.GCLOUD_VMWARE_CLUSTER


class GCloudInstance(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.GCLOUD_INSTANCE


class AzureFunctionLinux(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AZURE_FUNCTION_LINUX


class AzureFunctionWindows(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AZURE_FUNCTION_WINDOWS


class AzureCluster(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AZURE_CLUSTER


class AzureInstance(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AZURE_INSTANCE


class KubernetesService(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.KUBERNETES_SERVICE


class KubernetesPod(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.KUBERNETES_POD


class AwsDynamoDb(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_DYNAMO_DB


class AwsSqs(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_SQS


class AwsSns(TerraformComputeResource):

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_SNS


class AwsApiGatewayRestApi(TerraformComputeResource):
    description: Optional[str] = None

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_API_GATEWAY_REST_API


class AwsApiGatewayIntegration(TerraformComputeResource):
    rest_api_id: str
    uri: Optional[str] = None

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_API_GATEWAY_INTEGRATION

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers)

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        return super().get_references(references | {self.uri, self.rest_api_id})


# add new resources here


ALL_TERRAFORM_RESOURCES: dict[str, Type[TerraformComputeResource]] = {x.get_cloud_resource_type().value: x for x in
                                                                      TerraformComputeResource.__subclasses__()}
