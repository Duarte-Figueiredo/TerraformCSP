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

TF_RESOURCE_NAMES: set[str] = {"name", "function_name"}


# noinspection PyDefaultArgument
class TerraformComputeResource(TerraformResource):
    name: Optional[str] = None

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return super().get_identifiers(identifiers) | {self.name}

    # noinspection PyDefaultArgument,PyArgumentList
    @classmethod
    def process_hcl(cls, obj: dict[str, any],
                    additional_fields: dict[str, any] = {}) -> TerraformResource:
        terraform_resource_name: str = list(obj.keys())[0]
        obj: dict[str, any] = obj[terraform_resource_name]

        return cls(terraform_resource_name=terraform_resource_name,
                   **obj,
                   **additional_fields)


# noinspection PyDefaultArgument
class AwsLambda(TerraformComputeResource):
    role: Optional[str] = None
    env_variables: Optional[dict[str, Union[str, bool, int]]] = None

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return super().get_identifiers(identifiers) | {self.role}

    def get_references(self, references: set[Optional[str]] = set()) -> set[str]:
        str_env_variables: set[str] = set(
            filter(lambda x: x is str, self.env_variables)) if self.env_variables else set()
        return super().get_references(references | str_env_variables)

    @classmethod
    def process_hcl(cls, obj: dict[str, any],
                    additional_fields: dict[str, any] = {}) -> TerraformResource:
        data = next(iter(obj.values()))

        if ENVIRONMENT in data:
            env = data[ENVIRONMENT]
            if type(env) is dict:
                if VARIABLES in env:
                    additional_fields["env_variables"] = env[VARIABLES]
            elif type(env) is list:
                for item in env:
                    if VARIABLES in item:
                        additional_fields["env_variables"] = item[VARIABLES]

        return super().process_hcl(obj, additional_fields)

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_LAMBDA.value


class AwsCluster(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_CLUSTER.value


class AwsInstance(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_INSTANCE.value


class GCloudFunction(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.GCLOUD_FUNCTION.value


class GCloudVmWareCluster(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.GCLOUD_VMWARE_CLUSTER.value


class GCloudInstance(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.GCLOUD_INSTANCE.value


class AzureFunctionLinux(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_FUNCTION_LINUX.value


class AzureFunctionWindows(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_FUNCTION_WINDOWS.value


class AzureCluster(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_CLUSTER.value


class AzureInstance(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_INSTANCE.value


class KubernetesService(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.KUBERNETES_SERVICE.value


class KubernetesPod(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.KUBERNETES_POD.value


class AwsDynamoDb(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_DYNAMO_DB.value


class AwsSqs(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_SQS.value


class AwsSns(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_SNS.value


class AWSApiGatewayRestApi(TerraformComputeResource):
    description: Optional[str] = None

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_API_GATEWAY_REST_API.value


# noinspection PyDefaultArgument
class AWSApiGatewayIntegration(TerraformComputeResource):
    rest_api_id: str
    uri: Optional[str] = None

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_API_GATEWAY_INTEGRATION.value

    @classmethod
    def process_hcl(cls, obj: dict[str, any], additional_fields: dict[str, any] = {}) -> TerraformResource:
        return super().process_hcl(obj, additional_fields)

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return super().get_identifiers(identifiers | {self.rest_api_id})

    def get_references(self, references: set[Optional[str]] = set()) -> set[str]:
        return super().get_references(references | {self.uri})


# add new resources here


ALL_TERRAFORM_RESOURCES: dict[str, Type[TerraformComputeResource]] = {x.get_terraform_name(): x for x in
                                                                      TerraformComputeResource.__subclasses__()}
