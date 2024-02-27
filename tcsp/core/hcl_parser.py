import logging
from typing import Set

import hcl2
from lark import LarkError

from tcsp.core import Resource

MODULE = "module"
MODULE_SOURCE = "source"
TF_SUFFIX = ".tf"
TF_MAIN_FILE_NAME = "main.tf"

logger = logging.getLogger("hcl_parser")


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


def list_hcl_dependencies(resource: Resource) -> set[str]:
    hcl_dict: dict
    with open(resource.local_path, 'r') as file:
        try:
            hcl_dict = hcl2.load(file)
        except LarkError as e:
            logger.warning(f"Failed to parse '{resource.remote_resource.get_relative_path_with_name()}'")
            logger.debug(f"Failed to parse '{resource.remote_resource.get_relative_path_with_name()}'", exc_info=e)
            return set()

    detected_dependencies: set[str] = hcl_dependencies(hcl_dict)

    return detected_dependencies
