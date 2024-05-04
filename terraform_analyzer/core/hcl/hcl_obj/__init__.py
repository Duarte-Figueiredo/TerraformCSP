from typing import Optional

from pydantic import BaseModel


# noinspection PyDefaultArgument
class TerraformResource(BaseModel):
    terraform_resource_name: str

    @staticmethod
    def get_terraform_name() -> str:
        raise RuntimeError("Not implemented")

    def get_identifiers(self, identifiers: set[Optional[str]] = set()) -> set[str]:
        return set(filter(lambda x: x is not None, identifiers | {self.terraform_resource_name}))

    def get_references(self, references: set[Optional[str]] = set()) -> set[str]:
        return set(filter(lambda x: x is not None, references))
