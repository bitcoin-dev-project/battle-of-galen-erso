#!/usr/bin/env python3

import threading
import time

from commander import Commander


class Faucet(Commander):
    def set_test_params(self):
        self.num_nodes = 1
        self.addrs = []

    def add_options(self, parser):
        parser.description = (
            "Funds all armada nodes evenly with available miner funds"
        )
        parser.usage = "warnet run /path/to/faucet.py"


    def get_addr_from_ship(self, node):
        wallet = self.ensure_miner(node)
        addr = wallet.getnewaddress("bech32")
        self.addrs.append(addr)
        self.log.info(f"Got addr {addr} from tank {node.tank}")


    def get_addrs(self):
        ships = []
        for tank in self.nodes:
            if "armada" in tank.tank:
                ships.append(tank)
        self.log.info(f"Found armada ships:{[ship.tank for ship in ships]}")
        # Do this in parallel or it'll take forever
        for ship in ships:
            t = threading.Thread(target=lambda ship=ship: self.get_addr_from_ship(ship))
            t.daemon = False
            t.start()

        while len(self.addrs) < len(ships):
            self.log.info(f"Got {len(self.addrs)} addrs out of {len(ships)} needed")
            time.sleep(2)

        self.log.info(f"Got addrs for every armada ship!")


    def run_test(self):
        miner = self.tanks["miner"]
        miner_wallet = self.ensure_miner(miner)
        balances = miner_wallet.getbalances()
        trusted = balances["mine"]["trusted"]
        immature = balances["mine"]["immature"]
        self.log.info(f"Miner balances:\n\tTrusted: {trusted}\n\tImmature: {immature}")

        # Save at least 1.0 BTC for fees and a little spending money
        if trusted > 2:
            self.get_addrs()
            bal_sats = int(float(trusted - 1) * 1e8)
            bal_amt = bal_sats // len(self.addrs)
            amt = bal_amt / 1e8
            outputs = {}
            for addr in self.addrs:
                outputs[addr] = amt
            txid = miner_wallet.sendmany(dummy="", amounts=outputs)
            self.log.info(f"Sent {amt} each to {len(self.addrs)} addrs in tx: {txid}")


def main():
    Faucet().main()


if __name__ == "__main__":
    main()
