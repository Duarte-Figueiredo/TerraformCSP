from typing import Optional, Type

from pydantic import BaseModel

from terraform_analyzer.core.hcl import CloudResourceType


class TerraformPermission(BaseModel):
    terraform_resource_name: str

    @staticmethod
    def get_terraform_name() -> str:
        raise RuntimeError("Not implemented")

    def get_source(self) -> str:
        raise RuntimeError("Not implemented")

    def get_target(self) -> str:
        raise RuntimeError("Not implemented")


class AwsLambdaTerraformPermission(TerraformPermission):
    action: str
    function_name: str
    principal: str
    source_arn: Optional[str] = None

    @staticmethod
    def get_terraform_name() -> str:
        return CloudResourceType.AWS_LAMBDA_PERMISSION.value

    def get_source(self) -> str:
        return self.function_name

    def get_target(self) -> str:
        return self.source_arn if self.source_arn else self.principal


ALL_TERRAFORM_PERMISSIONS: dict[str, Type[TerraformPermission]] = {x.get_terraform_name(): x for x in
                                                                   [AwsLambdaTerraformPermission]}