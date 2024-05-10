from typing import Union

import matplotlib.pyplot as plt
import networkx as nx
from networkx import Graph

from terraform_analyzer.core.hcl import CloudResourceType
from terraform_analyzer.core.schema import NodeTf, GraphTf, ComponentTf

RELEVANT_TYPES: set[CloudResourceType] = {
    CloudResourceType.AWS_SNS,
    CloudResourceType.AWS_SQS,
    CloudResourceType.AWS_LAMBDA,
    CloudResourceType.AWS_DYNAMO_DB,
    CloudResourceType.AWS_API_GATEWAY_REST_API
}


def _get_relevant_transitive_connection(component: ComponentTf,
                                        graph: GraphTf,
                                        include_res: set[CloudResourceType] = None) -> list[ComponentTf]:
    visited_nodes: set[str] = {component.terraform_resource.get_qualified_name()}

    connections: list[ComponentTf] = []

    nodes_to_visit: list[Union[ComponentTf, NodeTf]] = graph.get_connected(component, filter_by=[ComponentTf])

    while nodes_to_visit:
        next_node = nodes_to_visit.pop(0)
        next_node_name = next_node.terraform_resource.get_qualified_name()

        if next_node_name in visited_nodes:
            continue
        visited_nodes.add(next_node_name)

        if include_res is None or next_node.terraform_resource.get_cloud_resource_type() in include_res:
            connections.append(next_node)
        else:
            nodes_to_visit.extend(graph.get_connected(next_node, filter_by=[ComponentTf]))

    return connections


def get_small_graph(tf_graph: GraphTf) -> Graph:
    graph = nx.Graph()

    relevant_component = list(
        filter(lambda x: x.terraform_resource.get_cloud_resource_type() in RELEVANT_TYPES, tf_graph.get_all_components()))

    for component in relevant_component:
        name = component.terraform_resource.get_qualified_name()

        graph.add_node(name, label=name)

    component: ComponentTf
    for component in relevant_component:
        node_name = str(component.terraform_resource.get_qualified_name())

        relevant_conns = _get_relevant_transitive_connection(component, tf_graph, RELEVANT_TYPES)
        other_node: ComponentTf
        # print(f"{node_name}->{[str(n) for n in relevant_component]}")

        for other_node in relevant_conns:
            if component == other_node:
                raise RuntimeError("Unexpected")

            other_node_name = other_node.terraform_resource.get_qualified_name()

            graph.add_edge(node_name, other_node_name)
    return graph


def get_big_graph(tf_graph: GraphTf) -> Graph:
    graph = nx.Graph()

    relevant_components: set[ComponentTf] = tf_graph.get_all_components()

    component: ComponentTf
    for component in relevant_components:
        name = component.terraform_resource.get_qualified_name()

        if component.terraform_resource.get_cloud_resource_type() in RELEVANT_TYPES:
            graph.add_node(name, label=name, color='green')
        else:
            graph.add_node(name, label=name)

    component: ComponentTf
    for component in relevant_components:
        node_name = str(component.terraform_resource.get_qualified_name())

        relevant_conns = _get_relevant_transitive_connection(component, tf_graph)
        other_node: ComponentTf
        # print(f"{node_name}->{[str(n) for n in relevant_nodes]}")

        for other_node in relevant_conns:
            if component == other_node:
                raise RuntimeError("Unexpected")

            other_node_name = other_node.terraform_resource.get_qualified_name()

            graph.add_edge(node_name, other_node_name)
    return graph


def show_graph(tf_graph: GraphTf):
    # Create two graphs
    g1 = get_small_graph(tf_graph)
    g2 = get_big_graph(tf_graph)

    font_size = 10
    node_size = 500
    k = 0.7  # node distance

    # Set up the subplot grid
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))  # 1 row, 2 columns

    # Draw the first graph on the left subplot
    ax1 = axes[0]
    pos = nx.spring_layout(g1, k)
    nx.draw_networkx(g1, pos, node_color='green', ax=ax1, with_labels=True, node_size=node_size, font_size=font_size)
    ax1.set_title('Simplified')
    ax1.axis('off')

    # Draw the second graph on the right subplot
    node_colors = [g2.nodes[node].get('color', 'red') for node in g2.nodes()]
    ax2 = axes[1]
    pos = nx.spring_layout(g2, k)
    nx.draw_networkx(g2, pos, node_color=node_colors, ax=ax2, with_labels=True, node_size=node_size,
                     font_size=font_size)
    ax2.set_title('Complete')
    ax2.axis('off')

    plt.tight_layout()
    plt.show()
