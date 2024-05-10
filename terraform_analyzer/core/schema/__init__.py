from typing import Union

from pydantic import BaseModel

from terraform_analyzer import TerraformResource
from terraform_analyzer.core.hcl import CloudResourceType

NODE_TYPES = {
    CloudResourceType.AWS_LAMBDA: "Lambda",
    CloudResourceType.AWS_API_GATEWAY_REST_API: "ApiGateway",
    CloudResourceType.AWS_DYNAMO_DB: "DynamoDB",
    CloudResourceType.AWS_SQS: "SQS",
    CloudResourceType.AWS_SNS: "SNS"
}


class FrozenModel(BaseModel):
    class Config:
        frozen = True


class ComponentTf(FrozenModel):
    terraform_resource: TerraformResource

    def __hash__(self) -> int:
        return hash(self.terraform_resource.get_qualified_name())


class NodeTf(BaseModel):
    name: str = ""
    cloud_resource_type: CloudResourceType
    components: set[ComponentTf] = set()

    def model_post_init(self, __context):
        self.name = NODE_TYPES.get(self.cloud_resource_type, "")

    def __hash__(self) -> int:
        return hash(self.cloud_resource_type)


class ConnectionTf(FrozenModel):
    a: Union[ComponentTf, NodeTf]
    b: Union[ComponentTf, NodeTf]
    justification: set[str]


class GraphTf(BaseModel):
    nodes: set[NodeTf]
    connections: list[ConnectionTf]

    def get_connections_types_str(self) -> set[str]:
        conns: set[str] = set()
        conn: ConnectionTf
        for conn in self.connections:
            conns.add(
                f"{conn.a.terraform_resource.get_cloud_resource_type()}->"
                f"{conn.b.terraform_resource.get_cloud_resource_type()}")
        return conns

    def get_connections_str(self) -> set[str]:
        conns: set[str] = set()
        for conn in self.connections:
            conns.add(
                f"{conn.a.terraform_resource.get_identifiers()}-{conn.justification}->"
                f"{conn.b.terraform_resource.get_identifiers()}")
        return conns

    def get_connected(self, node_or_component: Union[ComponentTf, NodeTf], filter_by=None) -> list[
        Union[ComponentTf, NodeTf]]:
        if filter_by is None:
            filter_by = [ComponentTf, NodeTf]
        connected: list[Union[ComponentTf, NodeTf]] = []

        for conn in self.connections:
            other_node: NodeTf
            if conn.a == node_or_component:
                other_node = conn.b
            elif conn.b == node_or_component:
                other_node = conn.a
            else:
                continue
            if other_node not in connected and type(other_node) in filter_by:
                connected.append(other_node)

        return connected

    def get_transitive_connected(self, component: ComponentTf,
                                 filter_by: set[CloudResourceType] = None) -> list[ComponentTf]:

        visited_nodes: set[str] = {component.terraform_resource.get_qualified_name()}

        connections: list[ComponentTf] = []

        nodes_to_visit: list[Union[ComponentTf, NodeTf]] = self.get_connected(component, filter_by=[ComponentTf])

        while nodes_to_visit:
            next_node = nodes_to_visit.pop(0)
            next_node_name = next_node.terraform_resource.get_qualified_name()

            if next_node_name in visited_nodes:
                continue
            visited_nodes.add(next_node_name)

            if filter_by is None or next_node.terraform_resource.get_cloud_resource_type() in filter_by:
                connections.append(next_node)
            else:
                nodes_to_visit.extend(self.get_connected(next_node, filter_by=[ComponentTf]))

        return connections

    def get_all_components(self) -> set[ComponentTf]:
        result = set()

        for node in self.nodes:
            result.update(node.components)

        return result
