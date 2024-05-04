import logging
from typing import Set, Any, Optional

import hcl2
from lark import LarkError

from terraform_analyzer.core import Resource, LocalResource
from terraform_analyzer.core.hcl import CLOUD_RESOURCE_TYPE_VALUES
from terraform_analyzer.core.hcl.timeout_utils import timeout

RESOURCE = "resource"
MODULE = "module"
MODULE_SOURCE = "source"
VARIABLE = "variable"
CONDITION = "condition"
DYNAMIC = "dynamic"
TF_SUFFIX = ".tf"
TF_MAIN_FILE_NAME = "main.tf"

logger = logging.getLogger("hcl_parser")


# CloudName Serverless      Cluster VPS                     Gateways    VPC     DB?
# AWS       Lambda          EKS     EC2
# GCloud    CloudFunctions  GKE     Google Compute Engine
# Azure     Azure Functions AKS     Azure Virtual Machines


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
        context_key = f"{path_context}_{key}"
        if key in CLOUD_RESOURCE_TYPE_VALUES and context_key.endswith(f"{RESOURCE}_{key}"):
            relevant_resources.append({key: value})
        elif key == VARIABLE and RESOURCE not in path_context:
            relevant_resources.append({context_key: value})
        elif key == CONDITION or key == DYNAMIC:
            continue
        else:
            if not value:
                continue
            elif type(value) is dict:
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


def list_hcl_resources(resource: LocalResource) -> list[dict[str, Any]]:
    hcl_dict: Optional[dict] = None

    try:
        hcl_dict = load_with_timeout(resource)
    except TimeoutError:
        logger.warning(f"Timed out while parsing {resource.get_full_path()}")

    if not hcl_dict:
        return []

    relevant_resources = extract_relevant_resources_from_dict(hcl_dict, resource.get_full_path())

    return relevant_resources
