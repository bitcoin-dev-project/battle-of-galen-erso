#!/usr/bin/env python3

import socket
import time

from commander import Commander

from test_framework.messages import (
    MSG_TX,
    CInv,
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


class Corn(Commander):
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
        # Get context from any node
        node = self.nodes[0]

        # This scenario requires some funds to spend. These should be available on Battlefield
        # On Scrimmage locally make sure you have mined at least 101 blocks using:
        # warnet run scenarios/miner_std.py --debug -- --interval=1
        victim = "TARGET_TANK_NAME.default.svc"

        addr = socket.gethostbyname(victim)

        self.log.info("Connecting to victim")
        attacker = P2PInterface()
        attacker.peer_connect(
            dstaddr=addr, dstport=node.p2pport, net=node.chain, timeout_factor=1
        )()
        attacker.wait_until(lambda: attacker.is_connected, check_connected=False)

        self.log.info("Creating first tx")

        # FILL ME IN
        # PERHAPS WITH A FELINE OP_CODE??
        script = CScript([])

        p2sh_address = script_to_p2sh(script)
        txid = node.sendtoaddress(p2sh_address, 0.0001)
        tx_hex = node.getrawtransaction(txid)
        first_tx = tx_from_hex(tx_hex)
        first_tx.rehash()

        vout = 0
        for v in first_tx.vout:
            if v.nValue == 0.0001:
                break
            vout += 1

        self.log.info("Creating spending tx")
        sec_tx = CTransaction()
        sec_tx.vin.append(
            CTxIn(COutPoint(first_tx.sha256, 0), scriptSig=CScript([script]))
        )
        sec_tx.vout.append(
            CTxOut(int(0.00009 * COIN), address_to_scriptpubkey(node.getnewaddress()))
        )

        for msg in [msg_tx(first_tx), msg_tx(sec_tx)]:
            self.log.info(f"Sending msg {msg}")
            attacker.send_and_ping(msg)


def main():
    Corn().main()


if __name__ == "__main__":
    main()
