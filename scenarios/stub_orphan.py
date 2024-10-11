#!/usr/bin/env python3

import socket
from time import sleep

from commander import Commander

# The entire Bitcoin Core test_framework directory is available as a library
from test_framework.messages import hash256, msg_tx
from test_framework.p2p import MAGIC_BYTES, P2PInterface
from test_framework.wallet import (
    MiniWallet,
    MiniWalletMode,
)


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
            "Demonstrate network reconnaissance using a scenario and P2PInterface"
        )
        parser.usage = "warnet run /path/to/reconnaissance.py"

    # Scenario entrypoint
    def run_test(self):
        self.log.info("Starting orphan scenario")
        self.log.info("Mining blocks to generate UTXOs")
        self.wallet = MiniWallet(self.nodes[0], mode=MiniWalletMode.RAW_P2PK)

        # Sorry about this wait, just need to mine a load, because of PoW on signet not every call ends in a block
        for i in range(3000):
            # this is a bit slow so done in 4 steps to prevent timeouts
            self.generate(self.wallet, 100)
            self.log.info(f"Mining attempt, {i+1} out of 3000")
        sleep(10)

        # Change this number to prevent someone from spending your coins
        # private_key = 5390
        # self.wallet._priv_key.set((private_key).to_bytes(32, "big"), True)
        # pub_key = self.wallet._priv_key.get_pubkey()
        # self.wallet._scriptPubKey = key_to_p2pk_script(pub_key.get_bytes())

        # Just like a typical Bitcoin Core functional test, this executes an
        # RPC on a node in the network. The actual node at self.nodes[0] may
        # be different depending on the user deploying the scenario. Users in
        # Warnet may have different namepsace access but everyone should always
        # have access to at least one node.
        peerinfo = self.nodes[0].getpeerinfo()
        for peer in peerinfo:
            # You can print out the the scenario logs with `warnet logs`
            # which have a list of all this node's peers' addresses and version
            self.log.info(f"{peer['addr']} {peer['subver']}")

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
            # make a transaction that doesn't arrive

            # make a transaction that spends the output of the above transaction

            # send the orphan, perhaps like this:
            # attacker.send_and_ping(msg_tx(tx_orphan["tx"]))

            self.log.info(f"Sent orphan {i+1} of 100")


def main():
    Orphan50().main()


if __name__ == "__main__":
    main()
