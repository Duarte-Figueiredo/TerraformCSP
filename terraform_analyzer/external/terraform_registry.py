import logging
from typing import List

from pydantic import BaseModel, TypeAdapter

from terraform_analyzer.external import request_session

TERRAFORM_REGISTRY_MODULES_URL = "https://registry.terraform.io/v1/modules"

logger = logging.getLogger("terraform_registry")


class TerraformModuleProviderDependency(BaseModel):
    name: str
    namespace: str
    source: str
    version: str


class TerraformModuleRoot(BaseModel):
    provider_dependencies: List[TerraformModuleProviderDependency]


class TerraformModuleInfo(BaseModel):
    id: str
    source: str
    root: TerraformModuleRoot


def get_source_code(dependency: str) -> str:
    module_url = f"{TERRAFORM_REGISTRY_MODULES_URL}/{dependency}"
    try:
        response = request_session.get(module_url)
        response_json = response.json()

        ta = TypeAdapter(TerraformModuleInfo)
        terraform_module_info = ta.validate_python(response_json)

        return terraform_module_info.source
    except Exception as ex:
        logger.error(f"Failed to grab source for terraform registry {module_url}")


if __name__ == '__main__':
    print(get_source_code("terraform-aws-modules/kms/aws"))
