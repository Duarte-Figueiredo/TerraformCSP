# resolves the variables
import os
import re
from typing import Any

from pydantic import BaseModel

RESOURCE = "_resource"
VARIABLE = "_variable"

DEFAULT = "default"
METADATA = "metadata"
NAME = "name"

VAR_PATTERN = re.compile('\$\{var\..*}')
VAR_NAME_PATTERN = re.compile('\$\{var\.(.*)}')


class Component(BaseModel):
    name: str
    terraform_resource_name: str
    resource_type: str


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


def _extract_name_of_component_from_metadata(obj: dict) -> str:
    if METADATA in obj and NAME in obj[METADATA][0]:
        return obj[METADATA][0][NAME]
    raise RuntimeError(f"Unable to extract name from metadata '{obj}")


def _extract_component_from_dict(d: dict) -> Component:
    for key, obj in d.items():
        resource_type: str = key
        terraform_resource_name: str = list(obj.keys())[0]
        obj: dict[str, any] = obj[terraform_resource_name]

        if "name" not in obj:
            name = _extract_name_of_component_from_metadata(obj)
        else:
            name = obj["name"]

        return Component(name=name,
                         terraform_resource_name=terraform_resource_name,
                         resource_type=resource_type)


def _extract_component_from_list(lis: list[any]) -> [Component]:
    components: [Component] = []
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


def _resolve_component(component: Component, variables: dict[str, str]) -> Component:
    var_name = VAR_NAME_PATTERN.findall(component.name)

    if var_name:
        var_value = variables[var_name[0]]
        real_component_name = re.sub(VAR_PATTERN, var_value, component.name)

        return Component(name=real_component_name,
                         terraform_resource_name=component.terraform_resource_name,
                         resource_type=component.resource_type)
    return component


def resolve(hcl_raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hcl_resolved_list: list[dict[str, Any]] = []

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
                variables: dict[str, str] = _load_variables(hcl_variables[path])
                value = hcl_raw[key]

                for resource in value:
                    new_comps: list[Component] = _extract_component_from_list(resource)

                    for unresolved_comp in new_comps:
                        resolved_comp = _resolve_component(unresolved_comp, variables)
                        tmp = resolved_comp.model_dump()
                        hcl_resolved_list.append(tmp)

    return hcl_resolved_list
