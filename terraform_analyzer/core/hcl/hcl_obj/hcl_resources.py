from typing import Type

from pydantic import BaseModel

from terraform_analyzer.core.hcl import CloudResourceType


class TerraformBaseResource(BaseModel):

    @staticmethod
    def get_terraform_name() -> str:
        raise RuntimeError("Not implemented")


class TerraformResource(TerraformBaseResource):
    name: str
    terraform_resource_name: str
    resource_type: str


class AwsLambda(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_LAMBDA.value


class AwsCluster(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_CLUSTER.value


class AwsInstance(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_INSTANCE.value


class GCloudFunction(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.GCLOUD_FUNCTION.value


class GCloudVmWareCluster(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.GCLOUD_VMWARE_CLUSTER.value


class GCloudInstance(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.GCLOUD_INSTANCE.value


class AzureFunctionLinux(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_FUNCTION_LINUX.value


class AzureFunctionWindows(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_FUNCTION_WINDOWS.value


class AzureCluster(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_CLUSTER.value


class AzureInstance(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AZURE_INSTANCE.value


class KubernetesService(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.KUBERNETES_SERVICE.value


class KubernetesPod(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.KUBERNETES_POD.value


class DynamoDb(TerraformResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.DYNAMO_DB.value


# add new resources here


ALL_TERRAFORM_RESOURCES: dict[str, Type[TerraformResource]] = {x.get_terraform_name(): x for x in
                                                               TerraformResource.__subclasses__()}
