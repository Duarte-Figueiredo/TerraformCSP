import logging
from typing import Set

import hcl2
from lark import LarkError

from tcsp.core import Resource
from tcsp.core.hcl import CLOUD_RESOURCE_TYPE_VALUES

MODULE = "module"
MODULE_SOURCE = "source"
VARIABLE = "variable"
TF_SUFFIX = ".tf"
TF_MAIN_FILE_NAME = "main.tf"

logger = logging.getLogger("hcl_parser")

# CloudName Serverless      Cluster VPS                     Gateways    VPC     DB?
# AWS       Lambda          EKS     EC2
# GCloud    CloudFunctions  GKE     Google Compute Engine
# Azure     Azure Functions AKS     Azure Virtual Machines


def sanitize_module_dependency(source: str) -> str:
    return source.replace("./", "")


def hcl_dependencies(tf: dict) -> Set[str]:
    dependencies: Set[str] = set()

    if MODULE in tf:
        modules: dict = tf[MODULE]

        for module in modules:
            resources: dict
            for resource in module.values():
                dependencies.add(sanitize_module_dependency(resource[MODULE_SOURCE]))

    return dependencies


def extract_relevant_resources_from_dict(hcl_dict: dict, path_context: str) -> list:
    if not hcl_dict:
        return []

    relevant_resources = []

    for key in hcl_dict.keys():
        context_key = f"{path_context}_{key}"
        if key in CLOUD_RESOURCE_TYPE_VALUES:
            relevant_resources.append({key: hcl_dict[key]})
        elif key == VARIABLE:
            relevant_resources.append({context_key: hcl_dict[key]})
        else:
            value = hcl_dict[key]

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


def list_hcl_dependencies(resource: Resource, hcl_resources: list) -> set[str]:
    hcl_dict: dict
    with open(resource.local_path, 'r') as file:
        try:
            hcl_dict = hcl2.load(file)
        except LarkError as e:
            logger.warning(f"Failed to parse '{resource.remote_resource.get_relative_path_with_name()}'")
            logger.debug(f"Failed to parse '{resource.remote_resource.get_relative_path_with_name()}'", exc_info=e)
            return set()

    relevant_resources = extract_relevant_resources_from_dict(hcl_dict, resource.remote_resource.get_relative_path())
    if relevant_resources:
        hcl_resources.extend(relevant_resources)

    detected_dependencies: set[str] = hcl_dependencies(hcl_dict)

    return detected_dependencies
