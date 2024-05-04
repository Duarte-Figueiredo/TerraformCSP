import json
import re
from typing import Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError, AliasChoices

from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource

JSONENCODE = "${jsonencode"
JSON_ENCODE_PATTERN = re.compile("\${jsonencode\((.*\))}")


class StatementIamCloudformation(BaseModel):
    action: Optional[Union[str, list[str]]] = Field(validation_alias=AliasChoices("Action", "action"), default=None)
    principal: Optional[Union[str, dict[str, Union[str, list[str]]]]] = Field(
        validation_alias=AliasChoices("Principal", "principal"),
        default=None)
    effect: str = Field(validation_alias=AliasChoices("Effect", "effect"))
    resource: Optional[Union[str, list[str]]] = Field(validation_alias=AliasChoices("Resource", "resource"),
                                                      default=None)

    def get_principal_reference(self) -> set[str]:
        if self.principal is None:
            return set()
        elif type(self.principal) is str:
            return set(self.principal)
        elif type(self.principal) is dict:
            references: set[str] = set()

            for item in self.principal.values():
                if type(item) is str:
                    references.add(item)
                elif type(item) is list:
                    references.update(item)
                else:
                    raise RuntimeError(f"Unsupported {type(item)}")

            return references
        else:
            raise RuntimeError(f"Unsupported {type(self.principal)}")

    def get_resource_reference(self) -> set[str]:
        if self.resource is None:
            return set()
        elif type(self.resource) is str or type(self.resource) is list:
            return set(self.resource)
        else:
            raise RuntimeError(f"Unsupported {type(self.resource)}")

    def get_references(self) -> set[str]:
        return self.get_principal_reference() | self.get_resource_reference()

    class Config:
        frozen = True


class IamCloudformation(BaseModel):
    version: str = Field(validation_alias=AliasChoices("Version", "version"))
    statement: Union[StatementIamCloudformation, list[StatementIamCloudformation]] = Field(
        validation_alias=AliasChoices("Statement", "statement"))

    def get_references(self) -> set[str]:

        if type(self.statement) is StatementIamCloudformation:
            return self.statement.get_references()
        elif type(self.statement) is list:
            tmp = set()

            for stat in self.statement:
                tmp.update(stat.get_references())

            return tmp
        else:
            raise RuntimeError(f"Unsupported {type(self.statement)}")

    class Config:
        frozen = True


def _handle_json_encode(s: str) -> str:
    return JSON_ENCODE_PATTERN.match(s)[1]


def _handle_policy(policy: str) -> Optional[IamCloudformation]:
    if policy.startswith(JSONENCODE):
        policy = _handle_json_encode(policy)

    try:
        d: dict = json.loads(policy)
        value = IamCloudformation(**d)
        return value
    except ValidationError as e:
        # TODO consume variables or files
        return None


class TerraformPermission(TerraformResource):
    pass


# noinspection PyDefaultArgument
class AwsLambdaPermission(TerraformPermission):
    action: str
    function_name: Optional[str] = None  # should be mandatory, but some repos don't have this set
    principal: str
    source_arn: Optional[str] = None

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_LAMBDA_PERMISSION.value

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return super().get_identifiers(identifiers | {self.function_name})

    def get_references(self, references: set[Optional[str]] = set()) -> set[str]:
        return super().get_references(references | {self.principal, self.source_arn})


# noinspection PyDefaultArgument
class AwsIamRole(TerraformPermission):
    name: Optional[str] = None
    assume_role_policy: str
    assume_role_policy_processed: Optional[IamCloudformation] = None

    def model_post_init(self, __context):
        self.assume_role_policy_processed = _handle_policy(self.assume_role_policy)

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_IAM_ROLE.value

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return super().get_identifiers(identifiers | {self.name})

    def get_references(self, references: set[Optional[str]] = set()) -> set[str]:
        if self.assume_role_policy_processed is not None:
            return super().get_references(references | self.assume_role_policy_processed.get_references())

        return super().get_references(references | {self.assume_role_policy})


# noinspection PyDefaultArgument
class AwsIamPolicy(TerraformPermission):
    name: Optional[str] = None
    policy: str
    policy_processed: Optional[IamCloudformation] = None

    def model_post_init(self, __context):
        self.policy_processed = _handle_policy(self.policy)

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_IAM_POLICY.value

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return super().get_identifiers(identifiers | {self.name})

    def get_references(self, references: set[Optional[str]] = set()) -> set[str]:
        if self.policy_processed is not None:
            return super().get_references(references | self.policy_processed.get_references())

        return super().get_references(references | {self.policy})


# noinspection PyDefaultArgument
class AwsIamRolePolicyAttachment(TerraformPermission):
    policy_arn: str
    role: str

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_IAM_ROLE_POLICY_ATTACHMENT.value

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return super().get_identifiers(identifiers | {self.policy_arn})

    def get_references(self, references: set[Optional[str]] = set()) -> set[str]:
        return super().get_references(references | {self.role})


ALL_TERRAFORM_PERMISSIONS: dict[str, Type[TerraformPermission]] = {x.get_terraform_name(): x for x in
                                                                   TerraformPermission.__subclasses__()}
