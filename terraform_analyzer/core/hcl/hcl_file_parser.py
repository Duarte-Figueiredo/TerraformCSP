import logging
from typing import Set, Optional

import hcl2
from lark import LarkError
from pydantic import ValidationError

from terraform_analyzer.core import Resource, LocalResource, utils
from terraform_analyzer.core.hcl import CLOUD_RESOURCE_TYPE_VALUES, TerraformSyntax, ModuleTf, ResourceTf, VariableTf
from terraform_analyzer.core.hcl.timeout_utils import timeout

RESOURCE = "resource"
MODULE = "module"
DATA = "data"
MODULE_SOURCE = "source"
VARIABLE = "variable"
CONDITION = "condition"
DYNAMIC = "dynamic"
TF_SUFFIX = ".tf"
TF_MAIN_FILE_NAME = "main.tf"

logger = logging.getLogger("hcl_parser")


def hcl_dependencies(tf: dict) -> Set[str]:
    dependencies: Set[str] = set()

    if MODULE in tf:
        modules: dict = tf[MODULE]

        for module in modules:
            resources: dict
            for resource in module.values():
                dependencies.add(resource[MODULE_SOURCE])

    return dependencies


def extract_relevant_resources_from_dict(hcl_dict: dict, path_context: str) -> list:
    if not hcl_dict:
        return []

    relevant_resources = []

    for key, value in hcl_dict.items():
        if not value:
            continue
        context_key = f"{path_context}_{key}"
        if type(value) in [list, dict]:
            if key in CLOUD_RESOURCE_TYPE_VALUES and \
                    (context_key.endswith(f"{RESOURCE}_{key}") or
                     context_key.endswith(f"{DATA}_{key}")):
                relevant_resources.append({key: value})
            elif key == VARIABLE and RESOURCE not in path_context:
                relevant_resources.append({context_key: value})
            elif key == CONDITION or key == DYNAMIC:
                continue
            elif key == MODULE:
                relevant_resources.append({context_key: value})

        if type(value) is dict:
            tmp = extract_relevant_resources_from_dict(value, context_key)
            if tmp:
                relevant_resources.append({context_key: tmp})
        elif type(value) is list or type(value) is set:
            tmp_list = []

            for obj in value:
                if obj and type(obj) is dict:
                    tmp = extract_relevant_resources_from_dict(obj, context_key)
                    if tmp:
                        tmp_list.append(tmp)

            if tmp_list:
                relevant_resources.append({context_key: tmp_list})

    return relevant_resources


@timeout(5)
def load_with_timeout(local_resource: LocalResource) -> Optional[dict]:
    with open(local_resource.full_path, 'r') as file:
        try:
            return hcl2.load(file)
        except (LarkError, UnicodeError) as e:
            logger.warning(f"Failed to parse '{local_resource.get_full_path()}'")
            logger.debug(f"Failed to parse '{local_resource.get_full_path()}'", exc_info=e)
    return None


def list_hcl_dependencies(resource: Resource) -> set[str]:
    hcl_dict: Optional[dict] = None

    try:
        hcl_dict = load_with_timeout(resource.local_resource)
    except TimeoutError:
        logger.warning(f"Timed out while parsing {resource.local_resource.get_full_path()}")

    if not hcl_dict:
        return set()

    detected_dependencies: set[str] = hcl_dependencies(hcl_dict)

    return detected_dependencies


def _map_to_terraform_syntax(context: str, resource_name: str, properties: dict[str, any]) -> Optional[TerraformSyntax]:
    if type(properties) is not dict:
        return None

    path: str
    try:
        if context.endswith(MODULE):
            path = context.removesuffix("_" + MODULE)
            return ModuleTf(path_context=path,
                            terraform_resource_name=resource_name,
                            **properties)
        elif context.endswith(RESOURCE) or context.endswith(DATA):
            path = context.removesuffix("_" + RESOURCE).removesuffix("_" + DATA)
            name = next(iter(properties))
            properties = properties[name]
            return ResourceTf(path_context=path,
                              terraform_resource_name=name,
                              resource_type=resource_name,
                              **properties)
        elif context.endswith(VARIABLE):
            path = context.removesuffix("_" + VARIABLE)
            return VariableTf(path_context=path,
                              terraform_resource_name=resource_name,
                              **properties)
        else:
            raise RuntimeError(f"Not implemented {context}")
    except ValidationError:
        logger.error(f"Failed to parse {resource_name} from '{properties}' over at {path}")
        return None


def list_hcl_resources(resource: LocalResource) -> list[TerraformSyntax]:
    hcl_dict: Optional[dict] = None

    try:
        hcl_dict = load_with_timeout(resource)
    except TimeoutError:
        logger.warning(f"Timed out while parsing {resource.get_full_path()}")

    if not hcl_dict:
        return []

    relevant_resources: list = extract_relevant_resources_from_dict(hcl_dict, resource.get_full_path())

    tf_syntax: list[TerraformSyntax] = []

    for rel_resource in relevant_resources:
        context: str
        for context, obj in rel_resource.items():
            if RESOURCE in context or DATA in context:
                for resources in obj:
                    if type(resources) is dict:
                        for resource_name, properties in resources.items():
                            tmp = _map_to_terraform_syntax(context, resource_name, properties)
                            if tmp:
                                tf_syntax.append(tmp)
                    elif type(resources) is list:
                        for res in resources:
                            for resource_name, properties in res.items():
                                tmp = _map_to_terraform_syntax(context, resource_name, properties)
                                if tmp:
                                    tf_syntax.append(tmp)
                    else:
                        raise RuntimeError(f"Unexpected '{type(resources)}")

            elif MODULE in context or VARIABLE in context:
                for resource_name, properties in utils.flat_list_dicts_to_dict(obj).items():
                    tmp = _map_to_terraform_syntax(context, resource_name, properties)
                    if tmp:
                        tf_syntax.append(tmp)

            else:
                logger.warning(f"Unexpected {context}")

    return tf_syntax
