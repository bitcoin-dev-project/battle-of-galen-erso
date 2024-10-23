#!/usr/bin/env python3

import socket
import time

from commander import Commander

# The entire Bitcoin Core test_framework directory is available as a library
from test_framework.messages import (
    hash256,
    msg_block,
    msg_ping,
)
from test_framework.p2p import MAGIC_BYTES, P2PInterface

from test_framework.blocktools import create_block, create_coinbase


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
class InvalidBlock(Commander):
    def set_test_params(self):
        # This setting is ignored but still required as
        # a sub-class of BitcoinTestFramework
        self.num_nodes = 1

    def add_options(self, parser):
        parser.description = "Send an invalid block to a node"
        parser.usage = "warnet run stub_invalid_block.py --debug"

    # Scenario entrypoint
    def run_test(self):
        def get_msg(message):
            if message:
                [print(f"Peer: {addr.ip}, Port: {addr.port}") for addr in message.addrs]

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

        best_block_hash = self.nodes[0].getbestblockhash()
        best_block = self.nodes[0].getblock(best_block_hash)
        best_block_time = best_block["time"]
        coinbase = create_coinbase(height=123)
        new_block = create_block(
            hashprev=int(best_block_hash, 16),
            coinbase=coinbase,
            ntime=best_block_time + 1,
        )
        # new_block.solve()
        new_block.hashMerkleRoot = 0xDEADBEEF
        msg = msg_block(new_block)

        # DEAR HACKERS: The invalid block msg has been made, send it now!

        ping = msg_ping()
        self.log.info(f"Ping: {attacker.ping_counter}")
        attacker.send_message(ping)
        time.sleep(3)
        self.log.info(f"Ping: {attacker.ping_counter}")

        attacker.wait_for_disconnect()
        self.log.info("Disconnected or timed out")


def main():
    InvalidBlock().main()


if __name__ == "__main__":
    main()
