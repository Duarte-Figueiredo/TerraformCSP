from typing import Optional

from pydantic import BaseModel, Field, AliasChoices

from terraform_analyzer.core.hcl import CloudResourceType


class TerraformResource(BaseModel):
    terraform_resource_name: str
    name: Optional[str] = Field(validation_alias=AliasChoices("name", "function_name"), default=None)

    @staticmethod
    def get_cloud_resource_type() -> CloudResourceType:
        raise RuntimeError("Not implemented")

    def get_qualified_name(self) -> str:
        qualified_name = self.get_terraform_identifier()
        if self.name:
            qualified_name = f"{qualified_name}.{self.name}"
        return qualified_name

    def get_terraform_identifier(self):
        return f"{self.get_cloud_resource_type().value}.{self.terraform_resource_name}"

    def get_identifiers(self, identifiers=None) -> set[str]:
        if identifiers is None:
            identifiers = set()

        service_name = self.get_cloud_resource_type().get_cloud_service_name()
        return set(filter(lambda x: x is not None, identifiers | {
            self.name,
            self.terraform_resource_name,
            '{' + service_name + '}' if service_name else None,
            self.get_terraform_identifier()
        }))

    def get_references(self, references=None) -> set[str]:
        if references is None:
            references = set()
        return set(filter(lambda x: x is not None, references))
