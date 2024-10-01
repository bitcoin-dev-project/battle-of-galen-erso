import os
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
    "25.0"
]

network_file = Path(os.path.dirname(__file__)).parent / "networks" / "battlefield_120" / "network.yaml"

def cycle_versions(versions):
    index = 0
    while True:
        yield versions[index]
        index = (index + 1) % len(versions)
version_generator = cycle_versions(VERSIONS)

with network_file.open() as f:
    network = yaml.safe_load(f)

for i, node in enumerate(network["nodes"]):
    node["image"]["tag"] = next(version_generator)
    node["name"] += f"-{TEAMS[i // 12]}"

with network_file.open("w") as f:
    yaml.dump(network, f)
