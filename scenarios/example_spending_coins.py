#!/usr/bin/env python3

import socket
import time

from commander import Commander

from test_framework.messages import (
    MSG_TX,
    CInv,
    hash256,
    tx_from_hex,
    msg_tx,
    COIN,
    CTxIn,
    COutPoint,
    CTxOut,
    CTransaction,
)
from test_framework.p2p import P2PInterface
from test_framework.script import CScript, OP_CAT
from test_framework.address import script_to_p2sh, address_to_scriptpubkey

class SpendingCoins(Commander):
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
        # get context from any node
        node = self.nodes[0]

        victim = "TARGET_TANK_NAME.default.svc"
        addr = socket.gethostbyname(victim)

        self.log.info("Connecting to victim")
        attacker = P2PInterface()
        attacker.peer_connect(
            dstaddr=addr, dstport=node.p2pport, net=node.chain, timeout_factor=1
        )()
        attacker.wait_until(lambda: attacker.is_connected, check_connected=False)

        utxos = node.listunspent()
        txid = int(utxos[0]["txid"], 16)
        vout = utxos[0]["vout"]

        self.log.info(f"utxos {utxos}")

        sec_tx = CTransaction()
        sec_tx.vin.append(CTxIn(COutPoint(txid, vout)))
        sec_tx.vout.append(
            CTxOut(int(0.00009 * COIN), address_to_scriptpubkey(node.getnewaddress()))
        )

        # raw_tx = node.create_raw_transaction(sec_tx.serialize())
        signed_tx = node.signrawtransactionwithwallet(sec_tx.serialize().hex())

        self.log.info(f"signed_tx {signed_tx}")

        tx = tx_from_hex(signed_tx["hex"])
        attacker.send_and_ping(msg_tx(tx))


def main():
    SpendingCoins().main()


if __name__ == "__main__":
    main()
