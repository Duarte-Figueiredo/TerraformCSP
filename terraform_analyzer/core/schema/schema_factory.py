import re
from typing import Union

from terraform_analyzer import TerraformResource
from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.schema import GraphTf, NodeTf, ComponentTf, ConnectionTf

TF_VARIABLE_PATTERN = re.compile("\${((?:[^\.]*)\.(?:[^\.]*)).*}")


def _parse_reference(reference: str) -> str:
    match = TF_VARIABLE_PATTERN.match(reference)
    return match.group(1) if match else reference


def _infer_connections(components: list[ComponentTf], nodes: set[NodeTf]) -> list[ConnectionTf]:
    result: list[ConnectionTf] = []
    c_n_identifier: dict[str, list[Union[ComponentTf, NodeTf]]] = {}

    for comp in components:
        identifiers = comp.terraform_resource.get_identifiers()
        for identifier in identifiers:
            c_n_identifier[identifier] = c_n_identifier.get(identifier, []) + [comp]

    for node in nodes:
        identifier = node.cloud_resource_type.get_service_permission_identifier()
        if identifier:
            assert identifier not in c_n_identifier
            c_n_identifier[identifier] = [node]

    for component in components:
        references = component.terraform_resource.get_references()

        for reference in references:
            parsed_ref = _parse_reference(reference)

            other_components_or_nodes = c_n_identifier.get(parsed_ref, [])
            for other_component_or_node in other_components_or_nodes:
                if component == other_component_or_node:
                    continue

                result.append(ConnectionTf(a=component,
                                           b=other_component_or_node,
                                           justification={parsed_ref}))

    return result


def _get_nodes(comps: list[ComponentTf]) -> set[NodeTf]:
    def _get_cloud_res_type_dict(components: list[ComponentTf]) -> dict[CloudResourceType, set[ComponentTf]]:
        result: dict[CloudResourceType, set[ComponentTf]] = {}

        for component in components:
            cloud_resource_type = component.terraform_resource.get_cloud_resource_type()
            tmp = result.get(cloud_resource_type, set())
            tmp.add(component)
            result[cloud_resource_type] = tmp

        return result

    cloud_res_type_dict = _get_cloud_res_type_dict(comps)

    nodes: set[NodeTf] = set()

    for cloud_res_type, associated_comp in cloud_res_type_dict.items():
        nodes.add(NodeTf(cloud_resource_type=cloud_res_type,
                         components=associated_comp))
    return nodes


def _get_components(terraform_resources: list[TerraformResource]) -> list[ComponentTf]:
    return list(map(lambda x: ComponentTf(terraform_resource=x), terraform_resources))


def build_graph(terraform_resources: list[TerraformResource]) -> GraphTf:
    components: list[ComponentTf] = _get_components(terraform_resources)

    nodes: set[NodeTf] = _get_nodes(components)

    connections: list[ConnectionTf] = _infer_connections(components, nodes)

    return GraphTf(nodes=nodes, connections=connections)
