# resolves the variables
import logging
import os
import re
from typing import Any, Optional, Union

from pydantic import ValidationError

from terraform_analyzer.core.hcl.hcl_obj import TerraformResource
from terraform_analyzer.core.hcl.hcl_obj.hcl_permissions import ALL_TERRAFORM_PERMISSIONS
from terraform_analyzer.core.hcl.hcl_obj.hcl_resources import ALL_TERRAFORM_RESOURCES

RESOURCE = "_resource"
VARIABLE = "_variable"

DEFAULT = "default"
METADATA = "metadata"
TAGS = "tags"
NAME = "name"

COUNT_INDEX = "count.index"

VAR_PATTERN = re.compile('\$\{var\.[^}]*}')
COUNT_PATTERN = re.compile('\$\{count\.[^}]*}')
VAR_NAME_PATTERN = re.compile('\$\{(?:(?:var)|(?:count))\.([^}]*)}')

TF_RESOURCE_NAMES: set[str] = {"name", "function_name"}

logger = logging.getLogger("hcl_resolver")


def _load_variables(hcl_variables: list[dict[str, any]]) -> dict[str, Union[str, int]]:
    var_name_value: dict[str, str] = {}
    for variables in hcl_variables:
        var_name: str
        var_obj: dict[str, any]
        for var_name, var_obj in variables.items():
            value: str
            if DEFAULT in var_obj and type(var_obj[DEFAULT] is str):
                value = var_obj[DEFAULT]
            else:
                value = "NO_DEFAULT_SET"
            var_name_value[var_name] = value

    return var_name_value


def _get_resource_name_and_nested_obj(d: dict[str, dict[str, any]]) -> dict[str, any]:
    if len(d) != 1:
        raise RuntimeError(f"Invalid dict {d}")

    terraform_resource_name = list(d.keys())[0]

    return {"terraform_resource_name": terraform_resource_name, **d[terraform_resource_name]}


def _extract_component_from_dict(d: dict) -> Optional[TerraformResource]:
    for key, obj in d.items():
        resource_type: str = key

        if resource_type in ALL_TERRAFORM_PERMISSIONS:
            clz = ALL_TERRAFORM_PERMISSIONS[resource_type]
            nested_obj = _get_resource_name_and_nested_obj(obj)

            return clz(**nested_obj)
        elif resource_type in ALL_TERRAFORM_RESOURCES:
            clz = ALL_TERRAFORM_RESOURCES[resource_type]
            return clz.process_hcl(obj)
        else:
            raise RuntimeError(
                f"Unable to resolve '{resource_type}', please create a terraform permission or resource class")

    raise RuntimeError(f"Empty component not allowed")


def _extract_component_from_list(lis: list[any]) -> [TerraformResource]:
    components: [TerraformResource] = []
    for item in lis:
        if type(item) is list:
            item: list
            components.extend(_extract_component_from_list(item))
        elif type(item) is dict:
            item: dict
            components.append(_extract_component_from_dict(item))
        else:
            raise RuntimeError(f"I don't know how to process this '{type(item)}'")

    return components


def _resolve_str(value: str, variables: dict[str, Union[str, int]]) -> str:
    detected_vars = VAR_NAME_PATTERN.findall(value)

    resolved_var = value
    for var in detected_vars:
        if "index" in var:
            resolved_var = re.sub(COUNT_PATTERN, "N", resolved_var)
        else:
            var_value: Union[str, int, None] = variables.get(var)

            if var_value:
                resolved_var = re.sub(VAR_PATTERN, str(var_value), resolved_var)

    return resolved_var


def _resolve_list(unresolved_list: list[any], variables: dict[str, Union[str, int]]) -> list[any]:
    if len(unresolved_list) == 0:
        return unresolved_list

    tmp: [any] = []
    for value in unresolved_list:
        tmp.append(_resolve_any(value, variables))

    return tmp


def _resolve_dict(unresolved_dict: dict[str, any], variables: dict[str, Union[str, int]]) -> dict[str, any]:
    resolved_dict = {}

    for key, value in unresolved_dict.items():
        resolved_dict[key] = _resolve_any(value, variables)

    return resolved_dict


def _resolve_any(value: any, variables: dict[str, Union[str, int]]) -> any:
    if value is None:
        return value
    elif type(value) is dict:
        return _resolve_dict(value, variables)
    elif type(value) is list:
        return _resolve_list(value, variables)
    elif type(value) is int or type(value) is bool:
        return value
    elif type(value) is str:
        return _resolve_str(value, variables)
    else:
        raise RuntimeError(f"unable to resolve {type(value)}")


def _resolve_component(component: TerraformResource, variables: dict[str, Union[str, int]]) -> TerraformResource:
    resolved_dict = _resolve_dict(component.dict(), variables)

    return type(component)(**resolved_dict)


def resolve(hcl_raw_list: list[dict[str, Any]]) -> list[TerraformResource]:
    hcl_resolved_list: list[TerraformResource] = []

    hcl_variables: dict[str, list[dict[str, any]]] = {}

    for hcl_raw in hcl_raw_list:
        for key in hcl_raw:
            if key.endswith(VARIABLE):
                path = os.path.dirname(key)
                value = hcl_raw[key]

                hcl_variables[path] = value

    for hcl_raw in hcl_raw_list:
        for key in hcl_raw.keys():
            if key.endswith(RESOURCE):
                path = os.path.dirname(key)

                variables: dict[str, Union[str, int]] = _load_variables(
                    hcl_variables[path]) if path in hcl_variables else {}
                value = hcl_raw[key]

                for resource in value:
                    try:
                        new_comps: list[Optional[TerraformResource]] = _extract_component_from_list(resource)
                    except ValidationError as e:
                        logger.error(f"Validation error on component {resource}", exc_info=e)
                        continue

                    for unresolved_comp in new_comps:
                        if unresolved_comp is None:
                            continue
                        resolved_comp = _resolve_component(unresolved_comp, variables)
                        hcl_resolved_list.append(resolved_comp)

    return hcl_resolved_list
