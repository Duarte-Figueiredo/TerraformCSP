from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field


class TerraformSyntax(BaseModel):
    path_context: str
    terraform_resource_name: str
    __pydantic_extra__: dict[str, any] = {}

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class VariableTf(TerraformSyntax):
    description: Optional[Union[str, int, float, bool]] = None
    default: Optional[any] = None
    var_type: Optional[str] = Field(alias="type", default=None)

    def model_post_init(self, __context):
        if type(self.default) not in [int, bool, float, str]:
            self.default = None


class ResourceTf(TerraformSyntax):
    resource_type: str

    class Config:
        frozen = True


class ModuleTf(TerraformSyntax):
    source: str

    def model_post_init(self, __context):
        self.source = self.source.removeprefix("./")


class CloudResourceType(str, Enum):
    AWS_LAMBDA = 'aws_lambda_function'
    AWS_CLUSTER = 'aws_eks_cluster'
    AWS_INSTANCE = 'aws_instance'

    GCLOUD_FUNCTION = 'google_cloudfunctions_function'
    GCLOUD_VMWARE_CLUSTER = 'google_vmwareengine_cluster'
    GCLOUD_INSTANCE = 'google_compute_instance'

    AZURE_FUNCTION_LINUX = "azurerm_linux_function_app"
    AZURE_FUNCTION_WINDOWS = "azurerm_windows_function_app"
    AZURE_CLUSTER = "azurerm_kubernetes_cluster"
    AZURE_INSTANCE = "azurerm_virtual_machine"

    KUBERNETES_SERVICE = "kubernetes_service"
    KUBERNETES_POD = "kubernetes_pod"

    AWS_DYNAMO_DB = "aws_dynamodb_table"
    # RDS_DB = "aws_db_instance"

    AWS_SQS = "aws_sqs_queue"
    AWS_SNS = "aws_sns_topic"

    # gateways
    AWS_API_GATEWAY_REST_API = "aws_api_gateway_rest_api"
    AWS_API_GATEWAY_INTEGRATION = "aws_api_gateway_integration"
    # AWS_API_GATEWAY_RESOURCE = "aws_api_gateway_resource"

    # permissions
    AWS_LAMBDA_PERMISSION = "aws_lambda_permission"
    AWS_IAM_ROLE = "aws_iam_role"
    AWS_IAM_POLICY = "aws_iam_policy"
    AWS_IAM_ROLE_POLICY_ATTACHMENT = "aws_iam_role_policy_attachment"
    AWS_IAM_POLICY_DOCUMENT = "aws_iam_policy_document"

    # event
    AWS_LAMBDA_EVENT_SOURCE_MAPPING = "aws_lambda_event_source_mapping"

    def get_cloud_service_name(self) -> Optional[str]:
        if self == self.AWS_LAMBDA:
            return "lambda"
        elif self == self.AWS_DYNAMO_DB:
            return "dynamodb"
        elif self == self.AWS_SNS:
            return "sns"
        elif self == self.AWS_SQS:
            return "sqs"
        elif self == self.AWS_API_GATEWAY_REST_API:
            return "apigateway"
        else:
            return None

    def get_service_permission_identifier(self) -> Optional[str]:
        if self == self.AWS_LAMBDA:
            return "lambda.amazonaws.com"
        elif self == self.AWS_DYNAMO_DB:
            return "dynamodb.amazonaws.com"
        elif self == self.AWS_SNS:
            return "sns.amazonaws.com"
        elif self == self.AWS_SQS:
            return "sqs.amazonaws.com"
        elif self == self.AWS_API_GATEWAY_REST_API:
            return "apigateway.amazonaws.com"
        else:
            return None


# TODO missing POD resource / apigateway / database

CLOUD_RESOURCE_TYPE_VALUES: set[str] = {x.value for x in CloudResourceType}
