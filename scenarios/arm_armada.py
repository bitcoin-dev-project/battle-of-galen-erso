#!/usr/bin/env python3

import threading
from commander import Commander
from time import sleep

FUNDS_PER_TANK = 10
FUNDING_TXS_COUNT = 10

class ArmArmada(Commander):
    def set_test_params(self):
        # This is just a minimum
        self.num_nodes = 0
        self.miners = []

    def add_options(self, parser):
        parser.description = "Send initial funds to all armada nodes"
        parser.usage = "warnet run /path/to/arm_armada.py"

    def run_test(self):
        self.log.info("Gathering armada nodes across all namespaces")
        tanks = []
        for node in self.nodes:
            if "armada" in node.tank:
                tanks.append(node)

        self.log.info("Waiting for miner spendable balance...")

        while True:
            bals = self.tanks["miner"].getbalances()
            self.log.info(bals)
            if bals["mine"]["trusted"] > FUNDS_PER_TANK * len(tanks):
                break
            else:
                sleep(5)

        self.log.info("Getting Armada wallet addresses...")
        outputs = {}

        def get_node_addr(self, node):
            while True:
                try:
                    node.createwallet("armada", descriptors=True)
                    address = node.getnewaddress()
                    self.log.info(f"Got wallet address {address} from {node.tank}")
                    outputs[address] = FUNDS_PER_TANK / FUNDING_TXS_COUNT
                    break
                except Exception as e:
                    self.log.info(
                        f"Couldn't get wallet address from {node.tank} because {e}, retrying in 5 seconds..."
                    )
                    sleep(5)

        addr_threads = [
            threading.Thread(target=get_node_addr, args=(self, node)) for node in tanks
        ]
        for thread in addr_threads:
            thread.start()

        all(thread.join() is None for thread in addr_threads)
        self.log.info(f"Got {len(outputs)} addresses from {len(tanks)} nodes (network size: {len(self.nodes)})")

        self.log.info("Funding Armada wallets...")

        for i in range(FUNDING_TXS_COUNT):
            self.log.info(f"Sending funding tx {i} of {FUNDING_TXS_COUNT}")
            res = self.tanks["miner"].sendmany(amounts=outputs, fee_rate=1)
            self.log.info(res)

        self.generatetoaddress(self.tanks["miner"], 1, self.tanks["miner"].getnewaddress())


def main():
    ArmArmada().main()

if __name__ == "__main__":
    main()
