import os
import random
import sys
import yaml

from pathlib import Path

TEAMS = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "violet",
    "black",
    "white",
    "grey",
    "brown"
]

VERSIONS = [
    "99.0.1-5k-inv",
    "99.1.0-invalid-blocks",
    "99.1.0-50-orphans",
    "99.0.1-no-mp-trim",
    "99.1.0-disabled-opcodes",
    "99.1.0-unknown-message",
    "0.16.1",
    "0.17.0",
    "0.19.2",
    "0.21.1",
    "24.2",
    "25.1"
]

network_dir = Path(os.path.dirname(__file__)).parent / "networks" / "battlefield_120"


def cycle_versions(versions):
    index = 0
    while True:
        yield versions[index]
        index = (index + 1) % len(versions)
version_generator = cycle_versions(VERSIONS)


def custom_graph(
    num_nodes: int,
    num_connections: int,
    version: str,
    datadir: Path,
    fork_observer: bool,
    fork_obs_query_interval: int,
    caddy: bool,
    logging: bool,
):
    try:
        datadir.mkdir(parents=False, exist_ok=True)
    except FileExistsError as e:
        print(e)
        print("Exiting network builder without overwriting")
        sys.exit(1)

    # Generate network.yaml
    nodes = []
    connections = set()

    for i in range(num_nodes):
        team = TEAMS[i // len(VERSIONS)]
        name = f"tank-{i:04d}-{team}"
        nodes.append({
            "name": name,
            "connect": [],
            "image": {"tag": next(version_generator)},
            "config": f"uacomment={team}"
        })

    for i, node in enumerate(nodes):
        # Add round-robin connection
        next_node_index = (i + 1) % num_nodes
        node["connect"].append(nodes[next_node_index]["name"])
        connections.add((i, next_node_index))

        # Add random connections
        available_nodes = list(range(num_nodes))
        available_nodes.remove(i)
        if next_node_index in available_nodes:
            available_nodes.remove(next_node_index)

        for _ in range(min(num_connections - 1, len(available_nodes))):
            random_node_index = random.choice(available_nodes)
            # Avoid circular loops of A -> B -> A
            if (random_node_index, i) not in connections:
                node["connect"].append(nodes[random_node_index]["name"])
                connections.add((i, random_node_index))
                available_nodes.remove(random_node_index)


    network_yaml_data = {"nodes": nodes}
    network_yaml_data["fork_observer"] = {
        "enabled": fork_observer,
        "configQueryInterval": fork_obs_query_interval,
    }
    network_yaml_data["caddy"] = {
        "enabled": caddy,
    }

    with open(os.path.join(datadir, "network.yaml"), "w") as f:
        yaml.dump(network_yaml_data, f, default_flow_style=False)

#     # Generate node-defaults.yaml
#     default_yaml_path = (
#         files("resources.networks").joinpath("fork_observer").joinpath("node-defaults.yaml")
#     )
#     with open(str(default_yaml_path)) as f:
#         defaults_yaml_content = yaml.safe_load(f)

#     # Configure logging
#     defaults_yaml_content["collectLogs"] = logging

#     with open(os.path.join(datadir, "node-defaults.yaml"), "w") as f:
#         yaml.dump(defaults_yaml_content, f, default_flow_style=False, sort_keys=False)

#     click.echo(
#         f"Project '{datadir}' has been created with 'network.yaml' and 'node-defaults.yaml'."
#     )



custom_graph(
    num_nodes=120,
    num_connections=8,
    version="27.0",
    datadir=network_dir,
    fork_observer=True,
    fork_obs_query_interval=20,
    caddy=True,
    logging=True)
