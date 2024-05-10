import json
import re
from json import JSONDecodeError
from typing import Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError, AliasChoices

from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource
from terraform_analyzer.external import aws_policy

JSONENCODE = "${jsonencode"
JSON_ENCODE_PATTERN = re.compile("\${jsonencode\((.*)\)}")

ACTION_REGEX = re.compile("(.*):.*")
AWS_SERVICE_PREFIX = "AWS_SERVICE"


class StatementIamCloudformation(BaseModel):
    action: Optional[Union[str, list[str]]] = Field(
        validation_alias=AliasChoices("Action", "action", "Actions", "actions"), default=None)

    principal: Optional[Union[str,
                              dict[str, Union[str, list[str]]],
                              list[dict[str, Union[str, list[str]]]]]] = Field(
        validation_alias=AliasChoices("Principal", "principal", "Principals", "principals"),
        default=None)

    effect: Optional[str] = Field(validation_alias=AliasChoices("Effect", "effect"), default="Allow")

    resource: Optional[Union[str, list[str]]] = Field(
        validation_alias=AliasChoices("Resource", "resource", "Resources", "resources"),
        default=None)

    def _get_principal_reference(self) -> set[str]:
        def _extract_from_dict(d: dict[str, Union[str, list[str]]]) -> set[str]:
            result: set[str] = set()
            for item in d.values():
                if type(item) is str:
                    result.add(item)
                elif type(item) is list:
                    result.update(item)
                else:
                    raise RuntimeError(f"Unsupported {type(item)}")
            return result

        if self.principal is None:
            return set()
        elif type(self.principal) is str:
            return set(self.principal)
        elif type(self.principal) is dict:
            return _extract_from_dict(self.principal)
        elif type(self.principal) is list:
            references: set[str] = set()

            for d in self.principal:
                references.update(_extract_from_dict(d))
            return references
        else:
            raise RuntimeError(f"Unsupported {type(self.principal)}")

    def _get_resource_reference(self) -> set[str]:
        if self.resource is None:
            return set()
        elif type(self.resource) is str or type(self.resource) is list:
            return set(self.resource)
        else:
            raise RuntimeError(f"Unsupported {type(self.resource)}")

    def _get_action_reference(self) -> set[str]:
        if self.action is None:
            return set()

        actions = set(self.action) if type(self.action) is str else self.action
        references: set[str] = set()

        for action in actions:
            match = ACTION_REGEX.match(action)
            if match is not None and match.group(1) is not None:
                references.add("{" + match[1].lower() + "}")

        return references

    def get_references(self) -> set[str]:
        resources_ref = self._get_resource_reference()
        principal_ref = self._get_principal_reference()

        if ("*" in resources_ref and (not principal_ref or '*' in principal_ref)) or \
                ("*" in principal_ref and (not resources_ref or '*' in resources_ref)):
            return self._get_action_reference()

        return self._get_principal_reference() | self._get_resource_reference()

    class Config:
        frozen = True


def get_statement_list_references(statements: list[StatementIamCloudformation]) -> [str]:
    tmp = set()

    for stat in statements:
        tmp.update(stat.get_references())

    return tmp


class IamCloudformation(BaseModel):
    version: str = Field(validation_alias=AliasChoices("Version", "version"))
    statement: Union[StatementIamCloudformation, list[StatementIamCloudformation]] = Field(
        validation_alias=AliasChoices("Statement", "statement"))

    def get_references(self) -> set[str]:

        if type(self.statement) is StatementIamCloudformation:
            return self.statement.get_references()
        elif type(self.statement) is list:
            return get_statement_list_references(self.statement)
        else:
            raise RuntimeError(f"Unsupported {type(self.statement)}")

    class Config:
        frozen = True


def _handle_json_encode(s: str) -> str:
    return JSON_ENCODE_PATTERN.match(s)[1]


def _handle_policy(policy: str) -> Optional[IamCloudformation]:
    raw_json_policy: str
    d: dict
    try:
        if policy.startswith("arn:aws"):
            d = aws_policy.get_aws_managed_policy(policy)
            return None if not d else IamCloudformation(**d)

        elif policy.startswith(JSONENCODE):
            raw_json_policy = _handle_json_encode(policy)
        else:
            raw_json_policy = policy

        d = json.loads(raw_json_policy)
        return IamCloudformation(**d)
    except (ValidationError, JSONDecodeError) as e:
        # TODO consume variables or files
        return None


class TerraformPermission(TerraformResource):
    pass


class AwsLambdaPermission(TerraformPermission):
    action: str
    principal: str
    source_arn: Optional[str] = None

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_LAMBDA_PERMISSION

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers)

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        return super().get_references(references | {self.principal, self.source_arn, self.name})


class AwsIamRole(TerraformPermission):
    name: Optional[str] = None
    assume_role_policy: str
    assume_role_policy_processed: Optional[IamCloudformation] = None

    def model_post_init(self, __context):
        self.assume_role_policy_processed = _handle_policy(self.assume_role_policy)

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_IAM_ROLE

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers | {self.name})

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        if self.assume_role_policy_processed is not None:
            return super().get_references(references | self.assume_role_policy_processed.get_references())

        return super().get_references(references | {self.assume_role_policy})


class AwsIamPolicy(TerraformPermission):
    name: Optional[str] = None
    policy: str
    policy_processed: Optional[IamCloudformation] = None

    def model_post_init(self, __context):
        self.policy_processed = _handle_policy(self.policy)

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_IAM_POLICY

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers | {self.name})

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        if self.policy_processed is not None:
            return super().get_references(references | self.policy_processed.get_references())

        return super().get_references(references | {self.policy})


class AwsIamRolePolicyAttachment(TerraformPermission):
    policy_arn: str
    role: str
    policy_processed: Optional[IamCloudformation] = None

    def model_post_init(self, __context):
        self.policy_processed = _handle_policy(self.policy_arn)

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_IAM_ROLE_POLICY_ATTACHMENT

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers)

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        if self.policy_processed is not None:
            return super().get_references(references | {self.role} | self.policy_processed.get_references())

        return super().get_references(references | {self.role} | {self.policy_arn})


class AwsIamPolicyDocument(TerraformPermission):
    statement: list[StatementIamCloudformation]

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        return CloudResourceType.AWS_IAM_POLICY_DOCUMENT

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()
        return super().get_identifiers(identifiers)

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        tmp = get_statement_list_references(self.statement)
        return super().get_references(references | tmp)


ALL_TERRAFORM_PERMISSIONS: dict[str, Type[TerraformPermission]] = {x.get_cloud_resource_type().value: x for x in
                                                                   TerraformPermission.__subclasses__()}
