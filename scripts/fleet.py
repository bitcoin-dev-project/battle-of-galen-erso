#!/usr/bin/env python3

import json
import os
import secrets
import sys
import yaml
from pathlib import Path
from random import choice

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from test_framework.key import ECKey  # noqa: E402
from test_framework.script_util import key_to_p2wpkh_script  # noqa: E402
from test_framework.wallet_util import bytes_to_wif  # noqa: E402
from test_framework.descriptors import descsum_create  # noqa: E402

TEAMS = [
    "aqua",
    "blue",
    "coffee",
    "emerald",
    "mint",
    "navy",
    "olive",
    "orange",
    "purple",
    "rust",
    "sapphire",
    "silver",
    "yellow"
]

VERSIONS = [
    "94.0.0-5k-inv",
    "98.0.0-invalid-blocks",
    "99.0.0-unknown-message",
    "97.0.0-50-orphans",
    "96.0.0-no-mp-trim",
    "95.0.0-disabled-opcodes",
    "0.21.1",
    "0.20.0",
    "0.19.2",
    "0.17.0",
    "0.16.1",
]

class Node:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.bitcoin_image = {"tag": "29.0"}
        self.rpcpassword = secrets.token_hex(16)

        self.addnode = []

    def to_obj(self):
        return {
            "name": self.name,
            "image": self.bitcoin_image,
            "global": {
                "rpcpassword": self.rpcpassword,
                "chain": self.game.chain
            },
            "addnode": self.addnode,
            "config":
                f'maxconnections=1000\n' +
                f'uacomment={self.name}\n' +
                'rpcauth=forkobserver:1418183465eecbd407010cf60811c6a0$d4e5f0647a63429c218da1302d7f19fe627302aeb0a71a74de55346a25d8057c\n ' +
                'rpcwhitelist=forkobserver:getchaintips,getblockheader,getblockhash,getblock,getnetworkinfo\n ' +
                'rpcwhitelistdefault=0\n ' +
                (f'signetchallenge={self.game.signetchallenge}\n' if self.game.chain == 'signet' else ''),
        }

class VulnNode(Node):
    def __init__(self, game, name):
        super().__init__(game, name)
        self.bitcoin_image = {"tag": "29.0-util"}

    def to_obj(self):
        obj = super().to_obj()
        obj.update({
            "collectLogs": True,
            "metricsExport": True,
            "metrics": 'blocks=getblockcount() mempool_size=getmempoolinfo()["size"] memused=getmemoryinfo()["locked"]["used"] memfree=getmemoryinfo()["locked"]["free"]',
        "resources": {
            "limits": {
                "cpu": "4000m",
                "memory": "1000Mi"
            },
            "requests": {
                "cpu": "100m",
                "memory": "200Mi"
            }
        }
        })
        return obj

class Miner(Node):
    def __init__(self, game):
        super().__init__(game, "miner")
        self.bitcoin_image = {"tag": "29.0-util"}

    def to_obj(self):
        obj = super().to_obj()
        obj.update({
            "startupProbe": {
                "failureThreshold": 10,
                "periodSeconds": 30,
                "successThreshold": 1,
                "timeoutSeconds": 60,
                "exec": {
                    "command": [
                        "/bin/sh",
                        "-c",
                        "bitcoin-cli createwallet miner && " +
                        f"bitcoin-cli importdescriptors {self.game.desc_string}"
                    ]
                }
            }
        })
        obj["config"] += 'coinstatsindex=1\n '
        obj["metricsExport"] = True
        obj["metrics"] = 'txrate=getchaintxstats(10)[\"txrate\"] utxosetsize=gettxoutsetinfo()[\"txouts\"]'
        return obj

class Game:
    def __init__(self, network_name, chain="signet"):
        print(f"\n**\n* Creating game {network_name}")
        self.network_name = network_name
        self.signetchallenge = None
        self.desc_string = None
        self.chain = chain
        self.generate_signet()

        self.miner = None
        self.nodes = []

    def generate_signet(self):
        # generate entropy
        secret = secrets.token_bytes(32)

        # derive private key and set global signet challenge (simple p2wpkh script)
        privkey = ECKey()
        privkey.set(secret, True)
        pubkey = privkey.get_pubkey().get_bytes()
        challenge = key_to_p2wpkh_script(pubkey)
        self.signetchallenge = challenge.hex()

        # output a bash script that executes warnet commands creating
        # a wallet on the miner node that can create signet blocks
        privkeywif=bytes_to_wif(secret)
        desc = descsum_create('combo(' + privkeywif + ')')
        desc_import = [{
            'desc': desc,
            'timestamp': 0
        }]
        desc_string = json.dumps(desc_import)
        self.desc_string = desc_string.replace("\"", "\\\"").replace(" ", "").replace("(", "\\(").replace(")", "\\)").replace(",", "\\,")

    def add_nodes(self, num_teams, targets_per_team):
        for i in range(num_teams):
            team = TEAMS[i]
            for v in range(targets_per_team):
                version = VERSIONS[v]
                node = VulnNode(self, f"tank-{len(self.nodes):04d}-{team}")
                node.bitcoin_image = {"tag": version}
                self.nodes.append(node)

    def add_miner(self):
        miner = Miner(self)
        self.miner = miner
        self.nodes.append(miner)

    def add_connections(self):
        for i in range(len(self.nodes)):
            # ensure one big ring of connections
            self.nodes[i].addnode.append(self.nodes[(i + 1) % len(self.nodes)].name)
            # add a few random, duplicates may happen but not a problem
            for _ in range(4):
                self.nodes[i].addnode.append(choice(self.nodes).name)

    def write(self):
        leaderboard_admin_key = secrets.token_hex(16)
        print("***********************")
        print("LEADERBOARD ADMIN KEY:")
        print(leaderboard_admin_key)
        print("***********************")
        network = {
            "nodes": [n.to_obj() for n in self.nodes],
            "caddy": {"enabled": True},
            "fork_observer": {
                "enabled": True,
                "configQueryInterval": 20
            },
            "services": [
                {
                    "title": "Leaderboard",
                    "path": "/leaderboard/",
                    "host": "leaderboard.default",
                    "port": 3000
                }
            ],
            "plugins": {
                "postDeploy": {
                    "leaderboard": {
                        "entrypoint": "../../plugins/leaderboard",
                        "admin_key": leaderboard_admin_key,
                        "next_public_asset_prefix": "/leaderboard"
                    }
                }
            }
        }
        self.write_network_yaml_dir("battlefields", network)

    def write_armada(self, num_tanks):
        armada = []
        for i in range(num_tanks):
            armada.append(Node(self, f"armada-{i}"))
        for n in armada:
            n.addnode.append("miner.default")
        self.write_network_yaml_dir("armadas", {"nodes": [n.to_obj() for n in armada]})

    def write_armies(self, n):
        data = { "namespaces": [] }
        for i in range(n):
            data['namespaces'].append({"name": "wargames-" + TEAMS[i]})
        default = {
            "users": [
                {
                    "name": "warnet-user",
                    "roles": [
                        "pod-viewer",
                        "pod-manager",
                        "ingress-viewer",
                        "ingress-controller-viewer"
                    ]
                }
            ]
        }
        self.write_yaml_dir("armies", data, default, "namespaces.yaml", "namespace-defaults.yaml")

    def write_network_yaml_dir(self, subdir, data):
        self.write_yaml_dir(subdir, data, {"warnet": self.network_name}, "network.yaml", "node-defaults.yaml")

    def write_yaml_dir(self, subdir, main_data, defaults_data, main_filename, defaults_filename):
        try:
            print(f"Creating {subdir} directory...")
            os.mkdir(Path(os.path.dirname(__file__)) / ".." / subdir / self.network_name)
        except FileExistsError:
            print("...already exists")
        with open(Path(os.path.dirname(__file__)) / ".." / subdir / self.network_name / main_filename, "w") as f:
            print(f"Writing {main_filename}...")
            yaml.dump(main_data, f, default_flow_style=False)
        with open(Path(os.path.dirname(__file__)) / ".." / subdir / self.network_name / defaults_filename, "w") as f:
            print(f"Writing {defaults_filename}...")
            yaml.dump(defaults_data, f, default_flow_style=False)


g = Game("signet_large", "signet")
g.add_nodes(len(TEAMS), len(VERSIONS))
g.add_miner()
g.add_connections()
g.write()
g.write_armada(3)
g.write_armies(len(TEAMS))

g = Game("regtest_small", "regtest")
g.add_nodes(1, 2)
g.add_miner()
g.add_connections()
g.write()
g.write_armada(1)
g.write_armies(1)

g = Game("signet_small", "signet")
g.add_nodes(1, 2)
g.add_miner()
g.add_connections()
g.write()
g.write_armada(1)
g.write_armies(1)
