# resolves the variables
import os
import re
from typing import Union, Any

from terraform_analyzer.core.hcl.hcl_obj.hcl_permissions import TerraformPermission, \
    ALL_TERRAFORM_PERMISSIONS
from terraform_analyzer.core.hcl.hcl_obj.hcl_resources import TerraformResource, ALL_TERRAFORM_RESOURCES

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


def _load_variables(hcl_variables: list[dict[str, any]]) -> dict[str, str]:
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


def _lower_case_obj_keys(obj: dict[str, any]) -> dict[str, any]:
    return {k.lower(): v for k, v in obj.items()}


def _extract_name_from_dict(obj: dict) -> str:
    nested_name_key = {METADATA, TAGS}
    obj_lower_case_key = _lower_case_obj_keys(obj)

    for key in nested_name_key:
        if key in obj_lower_case_key:
            nested_obj: Union[list[str], dict[str, str]] = obj_lower_case_key[key]

            if isinstance(nested_obj, list):
                nested_obj = nested_obj[0]
            elif not isinstance(nested_obj, dict):
                continue

            nested_obj = _lower_case_obj_keys(nested_obj)

            if NAME in nested_obj:
                return nested_obj[NAME]

    return "unknown"


def _get_resource_name_and_nested_obj(d: dict[str, dict[str, any]]) -> dict[str, any]:
    if len(d) != 1:
        raise RuntimeError(f"Invalid dict {d}")

    terraform_resource_name = list(d.keys())[0]

    return {"terraform_resource_name": terraform_resource_name, **d[terraform_resource_name]}


def _extract_component_from_dict(d: dict) -> Union[TerraformResource, TerraformPermission]:
    for key, obj in d.items():
        resource_type: str = key

        if resource_type in ALL_TERRAFORM_PERMISSIONS:
            clz = ALL_TERRAFORM_PERMISSIONS[resource_type]
            nested_obj = _get_resource_name_and_nested_obj(obj)

            return clz(**nested_obj)
        elif resource_type in ALL_TERRAFORM_RESOURCES:
            clz = ALL_TERRAFORM_RESOURCES[resource_type]

            terraform_resource_name: str = list(obj.keys())[0]
            obj: dict[str, any] = obj[terraform_resource_name]

            name_value = TF_RESOURCE_NAMES.intersection(obj.keys())

            if not name_value:
                name = _extract_name_from_dict(obj)
            elif len(name_value) == 1:
                name = obj[name_value.pop()]
            else:
                raise RuntimeError(f"Conflicting names detected '{name_value}' in '{obj.keys()}'")

            return clz(name=name,
                       terraform_resource_name=terraform_resource_name,
                       resource_type=resource_type)


def _extract_component_from_list(lis: list[any]) -> [Union[TerraformResource, TerraformPermission]]:
    components: [Union[TerraformResource, TerraformPermission]] = []
    for item in lis:
        if type(item) is list:
            item: list
            components.extend(_extract_component_from_list(item))
        elif type(item) is dict:
            item: dict
            components.append(_extract_component_from_dict(item))
        else:
            raise RuntimeError(f"I don't know how to process this '{item}'")

    return components


def _resolve_component(component: Union[TerraformResource, TerraformPermission], variables: dict[str, str]) -> Union[
    TerraformResource, TerraformPermission]:
    unresolved_dict = component.dict()
    resolved_dict = {}

    for key, value in unresolved_dict.items():
        if value is None:
            continue

        detected_vars = VAR_NAME_PATTERN.findall(value)

        variable_value = value
        for var in detected_vars:
            if "index" in var:
                variable_value = re.sub(COUNT_PATTERN, "N", variable_value)
            else:
                var_value = variables.get(var, "unresolved")
                variable_value = re.sub(VAR_PATTERN, var_value, variable_value)

        resolved_dict[key] = variable_value

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

                variables: dict[str, str] = _load_variables(hcl_variables[path]) if path in hcl_variables else {}
                value = hcl_raw[key]

                for resource in value:
                    new_comps: list[Union[TerraformResource, TerraformPermission]] = _extract_component_from_list(
                        resource)

                    for unresolved_comp in new_comps:
                        resolved_comp = _resolve_component(unresolved_comp, variables)
                        hcl_resolved_list.append(resolved_comp)

    return hcl_resolved_list
