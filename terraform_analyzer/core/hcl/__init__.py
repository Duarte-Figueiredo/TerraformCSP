from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


# provider "aws" {
#   version = "~> 2.0"
#   region  = var.region
# }
class CloudProviderType(str, Enum):
    AWS = 'aws'
    GCLOUD = 'gcloud'
    AZURE = 'azure'


class CloudResourceType(str, Enum):
    # AWS_LAMBDA = 'aws_lambda_function' this blows up
    AWS_CLUSTER = 'aws_eks_cluster'
    #AWS_INSTANCE = 'aws_instance'

    # GCLOUD_FUNCTION = 'google_cloudfunctions_function'
    # GCLOUD_VMWARE_CLUSTER = 'google_vmwareengine_cluster'
    # GCLOUD_INSTANCE = 'google_compute_instance'
    #
    # AZURE_FUNCTION_LINUX = "azurerm_linux_function_app"
    # AZURE_FUNCTION_WINDOWS = "azurerm_windows_function_app"
    # AZURE_CLUSTER = "azurerm_kubernetes_cluster"
    # AZURE_INSTANCE = "azurerm_virtual_machine"

    KUBERNETES_SERVICE = "kubernetes_service"
    KUBERNETES_POD = "kubernetes_pod"


# TODO missing POD resource / apigateway / database

CLOUD_RESOURCE_TYPE_VALUES: set[str] = {x.value for x in CloudResourceType}


class CloudResource(BaseModel):
    resource_type: CloudResourceType
    name: str


class CloudClusterResource(BaseModel):
    resource_type: CloudResourceType
    cloud_resources: List[CloudResource]


class CloudVpc(BaseModel):
    id: Optional[str]
    cloud_resources: List[CloudResource]


class CloudAccount(BaseModel):
    id: Optional[str]
    cloud_vpcs: List[CloudVpc]


class CloudProvider(BaseModel):
    cloud_provider_type: CloudProviderType
    cloud_accounts: List[CloudAccount]
