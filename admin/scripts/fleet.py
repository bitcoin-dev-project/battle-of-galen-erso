import json
import os
import random
import secrets
import sys
import yaml
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from test_framework.key import ECKey  # noqa: E402
from test_framework.script_util import key_to_p2wpkh_script  # noqa: E402
from test_framework.wallet_util import bytes_to_wif  # noqa: E402
from test_framework.descriptors import descsum_create  # noqa: E402

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
    "99.0.0-unknown-message",
    "98.0.0-invalid-blocks",
    "97.0.0-50-orphans",
    "96.0.0-no-mp-trim",
    "95.0.0-disabled-opcodes",
    "94.0.0-5k-inv",
    "0.21.1",
    "0.20.0",
    "0.19.2",
    "0.17.0",
    "0.16.1",
]

# generate and specify signet challenge (simple p2wpkh script)
secret=secrets.token_bytes(32)
privkey = ECKey()
privkey.set(secret, True)
pubkey = privkey.get_pubkey().get_bytes()
challenge = key_to_p2wpkh_script(pubkey)
signetchallenge=challenge.hex()
privkeywif=bytes_to_wif(secret)
desc = descsum_create('combo(' + privkeywif + ')')
desc_import = [{
    'desc': desc,
    'timestamp': 0
}]
desc_string = json.dumps(desc_import)
desc_string = desc_string.replace("\"", "\\\"").replace(" ", "").replace("(", "\\(").replace(")", "\\)").replace(",", "\\,")

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
    signetchallenge: str
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

    extra = f"\nsignetchallenge={signetchallenge}" if signetchallenge else ""

    # add central admin miner node
    nodes.append({
        "name": "miner",
        "addnode": [],
        "image": {"tag": "27.0"},
        "rpcpassword": secrets.token_hex(16),
        "config": f"maxconnections=1000\nuacomment=miner{extra}\ncoinstatsindex=1",
        "metrics": "txrate=getchaintxstats(10)[\"txrate\"] utxosetsize=gettxoutsetinfo()[\"txouts\"]"
    })
    num_nodes = teams * len(VERSIONS)
    for i in range(num_nodes):
        team = TEAMS[i // len(VERSIONS)]
        name = f"tank-{i:04d}-{team}"
        nodes.append({
            "name": name,
            "addnode": [],
            "image": {"tag": next(version_generator)},
            "rpcpassword": secrets.token_hex(16),
            "config": f"uacomment={team}{extra}"
        })

    for i, node in enumerate(nodes):
        # Add round-robin connection
        next_node_index = (i + 1) % num_nodes
        node["addnode"].append(nodes[next_node_index]["name"])
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
                node["addnode"].append(nodes[random_node_index]["name"])
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
    datadir=Path(os.path.dirname(__file__)).parent.parent / "networks" / "admin" / "battlefield",
    fork_observer=True,
    fork_obs_query_interval=20,
    caddy=True,
    logging=True,
    signetchallenge=signetchallenge)


custom_graph(
    teams=1,
    num_connections=8,
    version="27.0",
    datadir=Path(os.path.dirname(__file__)).parent.parent / "networks" / "scrimmage",
    fork_observer=True,
    fork_obs_query_interval=20,
    caddy=True,
    logging=True,
    signetchallenge="51")


custom_graph(
    teams=1,
    num_connections=8,
    version="27.0",
    datadir=Path(os.path.dirname(__file__)).parent.parent / "networks" / "admin" / "scrimmage_nologging",
    fork_observer=False,
    fork_obs_query_interval=20,
    caddy=False,
    logging=False,
    signetchallenge="51")

armies = {"namespaces": []}
for team in TEAMS:
    armies["namespaces"].append({"name": f"wargames-{team}"})
with open(Path(os.path.dirname(__file__)).parent / "namespaces" / "armies" / "namespaces.yaml", "w") as f:
    yaml.dump(armies, f, default_flow_style=False)

armadanet = {
    "nodes": [
        {"name": "armada-0", "config": f"signetchallenge={signetchallenge}"},
        {"name": "armada-1", "config": f"signetchallenge={signetchallenge}"},
        {"name": "armada-2", "config": f"signetchallenge={signetchallenge}"}
    ]
}
with open(Path(os.path.dirname(__file__)).parent.parent / "networks" / "armada" / "network.yaml", "w") as f:
    yaml.dump(armadanet, f, default_flow_style=False)

with open(Path(os.path.dirname(__file__)) / "miner_wallet.sh", "w") as f:
    f.write(f"warnet bitcoin rpc miner createwallet miner\nwarnet bitcoin rpc miner importdescriptors '{desc_string}'")
