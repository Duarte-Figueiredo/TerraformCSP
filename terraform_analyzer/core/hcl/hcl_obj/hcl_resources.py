from typing import Type

from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource


class TerraformComputeResource(TerraformResource):
    name: str
    terraform_resource_name: str
    resource_type: str


class AwsLambda(TerraformComputeResource):

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


class DynamoDb(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.DYNAMO_DB.value


class SQS(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.SQS.value


class SNS(TerraformComputeResource):

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.SNS.value


# add new resources here


ALL_TERRAFORM_RESOURCES: dict[str, Type[TerraformComputeResource]] = {x.get_terraform_name(): x for x in
                                                                      TerraformComputeResource.__subclasses__()}
