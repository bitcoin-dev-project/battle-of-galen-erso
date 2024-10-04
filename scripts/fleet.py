import os
import random
import secrets
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
    "0.20.0",
    "24.2",
    "25.1"
]


def cycle_versions(versions):
    index = 0
    while True:
        yield versions[index]
        index = (index + 1) % len(versions)
version_generator = cycle_versions(VERSIONS)


def custom_graph(
    teams: int,
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

    # add central admin miner node
    nodes.append({
        "name": "miner",
        "connect": [],
        "image": {"tag": "27.0"},
        "config": "maxconnections=1000\nuacomment=miner"
    })

    num_nodes = teams * len(VERSIONS)
    for i in range(num_nodes):
        team = TEAMS[i // len(VERSIONS)]
        name = f"tank-{i:04d}-{team}"
        nodes.append({
            "name": name,
            "connect": [],
            "image": {"tag": next(version_generator)},
            "rpcpassword": secrets.token_hex(16),
            "config": f"uacomment={team}"
        })

    for i, node in enumerate(nodes):
        # Add round-robin connection
        next_node_index = (i + 1) % num_nodes
        node["connect"].append(nodes[next_node_index]["name"])
        connections.add((i, next_node_index))

        # Add random connections including miner
        available_nodes = list(range(num_nodes + 1))
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


custom_graph(
    teams=len(TEAMS),
    num_connections=8,
    version="27.0",
    datadir=Path(os.path.dirname(__file__)).parent / "networks" / "battlefield",
    fork_observer=True,
    fork_obs_query_interval=20,
    caddy=True,
    logging=True)


custom_graph(
    teams=1,
    num_connections=8,
    version="27.0",
    datadir=Path(os.path.dirname(__file__)).parent / "networks" / "scrimmage",
    fork_observer=True,
    fork_obs_query_interval=20,
    caddy=True,
    logging=True)

armies = {"namespaces": []}
for team in TEAMS:
    armies["namespaces"].append({"name": f"wargames-{team}"})
with open(Path(os.path.dirname(__file__)).parent / "namespaces" / "armies" / "namespaces.yaml", "w") as f:
    yaml.dump(armies, f, default_flow_style=False)


