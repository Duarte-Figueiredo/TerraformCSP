# resolves the variables
import logging
import re
from typing import Optional, Union, List, Type

from pydantic import ValidationError

from terraform_analyzer.core import utils
from terraform_analyzer.core.hcl import TerraformSyntax, VariableTf, ModuleTf, ResourceTf
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource
from terraform_analyzer.core.hcl.hcl_obj.hcl_events import ALL_TERRAFORM_EVENTS
from terraform_analyzer.core.hcl.hcl_obj.hcl_permissions import ALL_TERRAFORM_PERMISSIONS
from terraform_analyzer.core.hcl.hcl_obj.hcl_resources import ALL_TERRAFORM_RESOURCES

COUNT_INDEX = "count.index"

VAR_PATTERN = re.compile('\$\{var\.[^}]*}')
COUNT_PATTERN = re.compile('\$\{count\.[^}]*}')
VAR_NAME_PATTERN = re.compile('\$\{(?:(?:var)|(?:count))\.([^}]*)}')

ALL_TERRAFORM: dict[str, Type[TerraformResource]] = ALL_TERRAFORM_RESOURCES | \
                                                    ALL_TERRAFORM_PERMISSIONS | \
                                                    ALL_TERRAFORM_EVENTS

logger = logging.getLogger("hcl_resolver")


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
    elif type(value) in [int, bool, float]:
        return value
    elif type(value) is str:
        return _resolve_str(value, variables).replace("'", '"')
    else:
        raise RuntimeError(f"unable to resolve {type(value)}")


def _resolve_component(component: TerraformResource, variables: dict[str, Union[str, int]]) -> TerraformResource:
    resolved_dict = _resolve_dict(component.dict(), variables)

    return type(component)(**resolved_dict)


def resolve_module(modules: list[dict[str, dict[str, any]]], path: str) -> list[(str, list[dict[str, any]])]:
    result: list[(str, list[dict[str, any]])] = []
    for module in modules:
        module_name = next(iter(module))
        module = module[module_name]
        if type(module) is not dict:
            raise RuntimeError(f"Unexpected type {type(module)}")

        module: dict

        local_ref = module.get("source", "")
        resolved_path = utils.resolve_path_local_reference(path, local_ref)

        del module["source"]
        if module:
            result.append((f"{resolved_path}_{module_name}", [module]))
    return result


def map_resource_tf_to_terraform_resource(resource_tf: ResourceTf,
                                          context_variable: List[VariableTf],
                                          module_variable: List[ModuleTf]) -> Optional[TerraformResource]:
    resource_type = resource_tf.resource_type

    fields = resource_tf.model_dump(include=resource_tf.model_fields)
    extras = resource_tf.model_extra

    assert fields.keys().isdisjoint(extras.keys())

    fields.update(extras)

    variables: dict[str, Union[str, bool, int, float]] = {}
    for var in context_variable:
        variables[var.terraform_resource_name] = var.default

    for module in module_variable:
        for key, value in module.model_extra.items():
            if type(value) in {str, bool, int, float}:
                # module variables should override local variables
                variables[key] = value

    resolved_fields = _resolve_any(fields, variables)

    if resource_type in ALL_TERRAFORM:
        clz = ALL_TERRAFORM[resource_type]
        try:
            return clz(**resolved_fields)
        except ValidationError as e:
            logger.error(f"Failed to parse {resource_type} from '{resolved_fields}': {str(e)}")
            return None
    else:
        raise RuntimeError(
            f"Unable to resolve '{resource_type}', please create a terraform permission or resource class")


def resolve(tf_syntax: List[TerraformSyntax]) -> list[TerraformResource]:
    result: [TerraformResource] = []

    # noinspection PyTypeChecker
    variables: list[VariableTf] = list(filter(lambda x: type(x) is VariableTf, tf_syntax))

    # noinspection PyTypeChecker
    modules: list[ModuleTf] = list(filter(lambda x: type(x) is ModuleTf, tf_syntax))

    # noinspection PyTypeChecker
    resources: list[ResourceTf] = list(filter(lambda x: type(x) is ResourceTf, tf_syntax))

    processed_resources: list[ResourceTf] = []

    for module in modules:
        context = module.source
        context_variables: list[VariableTf] = list(filter(lambda x: context in x.path_context, variables))

        parameterized_resources = []

        for resource in resources:
            # TODO remove full path from resource.path_context
            if context in resource.path_context:
                parameterized_resources.append(resource)
                processed_resources.append(resource)

        param_res: ResourceTf
        for param_res in parameterized_resources:
            tmp = map_resource_tf_to_terraform_resource(param_res, context_variables, [module])
            if tmp:
                result.append(tmp)

    for resource in resources:
        if resource in processed_resources:
            continue
        context = resource.path_context

        context_modules: list[ModuleTf] = list(filter(lambda x: x.source in context, modules))
        context_variables: list[VariableTf] = list(filter(lambda x: context in x.path_context, variables))

        tmp = map_resource_tf_to_terraform_resource(resource, context_variables, context_modules)
        if tmp:
            result.append(tmp)

    return result
