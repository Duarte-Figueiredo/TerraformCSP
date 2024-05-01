from typing import Type, Union, Optional

from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource

DEFAULT = "default"
METADATA = "metadata"
TAGS = "tags"
NAME = "name"
ENVIRONMENT = "environment"
VARIABLES = "variables"

TF_RESOURCE_NAMES: set[str] = {"name", "function_name"}


def _lower_case_obj_keys(obj: dict[str, any]) -> dict[str, any]:
    return {k.lower(): v for k, v in obj.items()}


def _extract_name_from_dict(obj: dict) -> str:
    nested_name_key = {METADATA, TAGS}
    obj_lower_case_key = _lower_case_obj_keys(obj)

    for key in nested_name_key:
        if key in obj_lower_case_key:
            nested_obj: Union[list[str], dict[str, str]] = obj_lower_case_key[key]

            if isinstance(nested_obj, list):
                nested_obj = nested_obj[0]
            elif not isinstance(nested_obj, dict):
                continue

            nested_obj = _lower_case_obj_keys(nested_obj)

            if NAME in nested_obj:
                return nested_obj[NAME]

    return "unnamed"


class TerraformComputeResource(TerraformResource):
    name: Optional[str] = None

    @staticmethod
    def _extract_name(obj: dict[str, any]) -> str:
        name_value = TF_RESOURCE_NAMES.intersection(obj.keys())

        if not name_value:
            return _extract_name_from_dict(obj)
        elif len(name_value) == 1:
            return obj[name_value.pop()]
        else:
            raise RuntimeError(f"Conflicting names detected '{name_value}' in '{obj.keys()}'")

    # noinspection PyDefaultArgument
    @classmethod
    def process_hcl(cls, obj: dict[str, any],
                    additional_fields: dict[str, any] = {}) -> TerraformResource:

        terraform_resource_name: str = list(obj.keys())[0]
        obj: dict[str, any] = obj[terraform_resource_name]

        name = TerraformComputeResource._extract_name(obj)

        return cls(name=name,
                   terraform_resource_name=terraform_resource_name,
                   **additional_fields)


class AwsLambda(TerraformComputeResource):
    env_variables: Optional[dict[str, Union[str, bool, int]]] = None

    @classmethod
    def process_hcl(cls, obj: dict[str, any],
                    additional_fields: dict[str, any] = {}) -> TerraformResource:
        data = next(iter(obj.values()))

        if ENVIRONMENT in data and VARIABLES in next(iter(data[ENVIRONMENT])):
            variables: any = next(iter(data[ENVIRONMENT]))[VARIABLES]
            if type(variables) is dict:
                additional_fields["env_variables"] = variables

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

    @staticmethod
    def get_terraform_name() -> str:
        return "????"  # CloudResourceType.AWS_API_GATEWAY_REST_API.value


# add new resources here


ALL_TERRAFORM_RESOURCES: dict[str, Type[TerraformComputeResource]] = {x.get_terraform_name(): x for x in
                                                                      TerraformComputeResource.__subclasses__()}
