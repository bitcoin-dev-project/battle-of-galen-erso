#!/usr/bin/env python3

import socket
import time
from commander import Commander
import copy
import abc
from typing import Optional

from test_framework.blocktools import (
    create_block,
    create_coinbase,
    create_tx_with_script,
)
from test_framework.messages import (
    CBlock,
    COutPoint,
    CTransaction,
    CTxIn,
    hash256,
    SEQUENCE_FINAL,
    msg_block,
)
from test_framework.p2p import P2PDataStore
from test_framework.script import (
    CScript,
    OP_DROP,
    OP_TRUE,
    sign_input_legacy,
)
from test_framework.wallet_util import generate_keypair
from test_framework.p2p import MAGIC_BYTES, P2PInterface


def get_signet_network_magic_from_node(node):
    template = node.getblocktemplate({"rules": ["segwit", "signet"]})
    challenge = template["signet_challenge"]
    challenge_bytes = bytes.fromhex(challenge)
    data = len(challenge_bytes).to_bytes() + challenge_bytes
    digest = hash256(data)
    return digest[0:4]


class BadTxTemplate:
    """Allows simple construction of a certain kind of invalid tx. Base class to be subclassed."""

    __metaclass__ = abc.ABCMeta

    # The expected error code given by bitcoind upon submission of the tx.
    reject_reason: Optional[str] = ""

    # Only specified if it differs from mempool acceptance error.
    block_reject_reason = ""

    # Do we expect to be disconnected after submitting this tx?
    expect_disconnect = False

    # Is this tx considered valid when included in a block, but not for acceptance into
    # the mempool (i.e. does it violate policy but not consensus)?
    valid_in_block = False

    def __init__(self, *, spend_tx=None, spend_block=None):
        self.spend_tx = spend_block.vtx[0] if spend_block else spend_tx
        self.spend_avail = sum(o.nValue for o in self.spend_tx.vout)
        self.valid_txin = CTxIn(COutPoint(self.spend_tx.sha256, 0), b"", SEQUENCE_FINAL)

    @abc.abstractmethod
    def get_tx(self, *args, **kwargs):
        """Return a CTransaction that is invalid per the subclass."""
        pass


class OutputMissing(BadTxTemplate):
    reject_reason = "bad-txns-vout-empty"
    expect_disconnect = True

    def get_tx(self):
        tx = CTransaction()
        tx.vin.append(self.valid_txin)
        tx.calc_sha256()
        return tx


class InputMissing(BadTxTemplate):
    reject_reason = "bad-txns-vin-empty"
    expect_disconnect = True

    # We use a blank transaction here to make sure
    # it is interpreted as a non-witness transaction.
    # Otherwise the transaction will fail the
    # "surpufluous witness" check during deserialization
    # rather than the input count check.
    def get_tx(self):
        tx = CTransaction()
        tx.calc_sha256()
        return tx


def iter_all_templates():
    """Iterate through all bad transaction template types."""
    return BadTxTemplate.__subclasses__()


#  Use this class for tests that require behavior other than normal p2p behavior.
#  For now, it is used to serialize a bloated varint (b64).
class CBrokenBlock(CBlock):
    def initialize(self, base_block):
        self.vtx = copy.deepcopy(base_block.vtx)
        self.hashMerkleRoot = self.calc_merkle_root()

    def serialize(self, with_witness=False):
        r = b""
        r += super(CBlock, self).serialize()
        r += (255).to_bytes(1, "little") + len(self.vtx).to_bytes(8, "little")
        for tx in self.vtx:
            if with_witness:
                r += tx.serialize_with_witness()
            else:
                r += tx.serialize_without_witness()
        return r

    def normal_serialize(self):
        return super().serialize()


DUPLICATE_COINBASE_SCRIPT_SIG = b"\x01\x78"  # Valid for block at height 120


class InvalidBlockTest(Commander):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.extra_args = [
            [
                "-acceptnonstdtxn=1",  # This is a consensus block test, we don't care about tx policy
                "-testactivationheight=bip34@2",
            ]
        ]

    def run_test(self):
        node = self.nodes[0]  # convenience reference to the node

        self.bootstrap_p2p()  # Add one p2p connection to the node

        self.block_heights = {}
        self.coinbase_key, self.coinbase_pubkey = generate_keypair()
        self.tip = None
        self.blocks = {}
        self.genesis_hash = int(self.nodes[0].getbestblockhash(), 16)
        self.block_heights[self.genesis_hash] = 0
        self.spendable_outputs = []

        # Create a new block
        b_dup_cb = self.next_block("dup_cb")
        b_dup_cb.vtx[0].vin[0].scriptSig = DUPLICATE_COINBASE_SCRIPT_SIG
        b_dup_cb.vtx[0].rehash()
        duplicate_tx = b_dup_cb.vtx[0]
        b_dup_cb = self.update_block("dup_cb", [])
        self.send_blocks([b_dup_cb])

        b0 = self.next_block(0)
        self.save_spendable_output()
        self.send_blocks([b0])

        # These constants chosen specifically to trigger an immature coinbase spend
        # at a certain time below.
        NUM_BUFFER_BLOCKS_TO_GENERATE = 99
        NUM_OUTPUTS_TO_COLLECT = 33

        # Allow the block to mature
        blocks = []
        for i in range(NUM_BUFFER_BLOCKS_TO_GENERATE):
            blocks.append(self.next_block(f"maturitybuffer.{i}"))
            self.save_spendable_output()
        self.send_blocks(blocks)

        # collect spendable outputs now to avoid cluttering the code later on
        out = []
        for _ in range(NUM_OUTPUTS_TO_COLLECT):
            out.append(self.get_spendable_output())

        # Start by building a couple of blocks on top (which output is spent is
        # in parentheses):
        #     genesis -> b1 (0) -> b2 (1)
        b1 = self.next_block(1, spend=out[0])
        self.save_spendable_output()

        b2 = self.next_block(2, spend=out[1])
        self.save_spendable_output()

        self.send_blocks([b1, b2], timeout=4)

        # Select a txn with an output eligible for spending. This won't actually be spent,
        # since we're testing submission of a series of blocks with invalid txns.
        attempt_spend_tx = out[2]

        # Submit blocks for rejection, each of which contains a single transaction
        # (aside from coinbase) which should be considered invalid.
        for TxTemplate in iter_all_templates():
            template = TxTemplate(spend_tx=attempt_spend_tx)

            if template.valid_in_block:
                continue

            self.log.info(f"Reject block with invalid tx: {TxTemplate.__name__}")
            blockname = f"for_invalid.{TxTemplate.__name__}"
            self.next_block(blockname)
            badtx = template.get_tx()
            if TxTemplate != InputMissing:
                self.sign_tx(badtx, attempt_spend_tx)
            badtx.rehash()
            badblock = self.update_block(blockname, [badtx])
            self.send_blocks(
                [badblock],
                success=False,
                reject_reason=(template.block_reject_reason or template.reject_reason),
                reconnect=True,
                timeout=2,
            )

            self.move_tip(2)

    # Helper methods
    ################

    def add_transactions_to_block(self, block, tx_list):
        [tx.rehash() for tx in tx_list]
        block.vtx.extend(tx_list)

    # this is a little handier to use than the version in blocktools.py
    def create_tx(self, spend_tx, n, value, output_script=None):
        if output_script is None:
            output_script = CScript([OP_TRUE, OP_DROP] * 15 + [OP_TRUE])
        return create_tx_with_script(
            spend_tx, n, amount=value, script_pub_key=output_script
        )

    # sign a transaction, using the key we know about
    # this signs input 0 in tx, which is assumed to be spending output 0 in spend_tx
    def sign_tx(self, tx, spend_tx):
        scriptPubKey = bytearray(spend_tx.vout[0].scriptPubKey)
        if scriptPubKey[0] == OP_TRUE:  # an anyone-can-spend
            tx.vin[0].scriptSig = CScript()
            return
        sign_input_legacy(tx, 0, spend_tx.vout[0].scriptPubKey, self.coinbase_key)

    def create_and_sign_transaction(self, spend_tx, value, output_script=None):
        if output_script is None:
            output_script = CScript([OP_TRUE])
        tx = self.create_tx(spend_tx, 0, value, output_script=output_script)
        self.sign_tx(tx, spend_tx)
        tx.rehash()
        return tx

    def next_block(
        self, number, spend=None, additional_coinbase_value=0, *, script=None, version=4
    ):
        if script is None:
            script = CScript([OP_TRUE])
        if self.tip is None:
            base_block_hash = self.genesis_hash
            block_time = int(time.time()) + 1
        else:
            base_block_hash = self.tip.sha256
            block_time = self.tip.nTime + 1
        # First create the coinbase
        height = self.block_heights[base_block_hash] + 1
        coinbase = create_coinbase(height, self.coinbase_pubkey)
        coinbase.vout[0].nValue += additional_coinbase_value
        coinbase.rehash()
        if spend is None:
            block = create_block(base_block_hash, coinbase, block_time, version=version)
        else:
            coinbase.vout[0].nValue += (
                spend.vout[0].nValue - 1
            )  # all but one satoshi to fees
            coinbase.rehash()
            tx = self.create_tx(spend, 0, 1, output_script=script)  # spend 1 satoshi
            self.sign_tx(tx, spend)
            tx.rehash()
            block = create_block(
                base_block_hash, coinbase, block_time, version=version, txlist=[tx]
            )
        # Block is created. Find a valid nonce.
        block.solve()
        self.tip = block
        self.block_heights[block.sha256] = height
        assert number not in self.blocks
        self.blocks[number] = block
        return block

    # save the current tip so it can be spent by a later block
    def save_spendable_output(self):
        self.log.debug(f"saving spendable output {self.tip.vtx[0]}")
        self.spendable_outputs.append(self.tip)

    # get an output that we previously marked as spendable
    def get_spendable_output(self):
        self.log.debug(f"getting spendable output {self.spendable_outputs[0].vtx[0]}")
        return self.spendable_outputs.pop(0).vtx[0]

    # move the tip back to a previous block
    def move_tip(self, number):
        self.tip = self.blocks[number]

    # adds transactions to the block and updates state
    def update_block(self, block_number, new_transactions):
        block = self.blocks[block_number]
        self.add_transactions_to_block(block, new_transactions)
        old_sha256 = block.sha256
        block.hashMerkleRoot = block.calc_merkle_root()
        block.solve()
        # Update the internal state just like in next_block
        self.tip = block
        if block.sha256 != old_sha256:
            self.block_heights[block.sha256] = self.block_heights[old_sha256]
            del self.block_heights[old_sha256]
        self.blocks[block_number] = block
        return block

    def bootstrap_p2p(self, timeout=10):
        """Add a P2P connection to the node.

        Helper to connect and wait for version handshake."""

        chain = self.nodes[0].chain

        # We pick a node on the network to attack
        # We know this one is vulnderable to an invalid block based on it's subver
        # Use either reconnaisance or ForkObserver UI to find vulnerable nodes
        # Change this to your teams colour if running in the battleground
        victim = "tank-0001-red.default.svc"

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
        self.log.info(f"Attacking {dstaddr}:{dstport}")
        attacker = P2PDataStore()
        attacker.peer_connect(
            dstaddr=dstaddr, dstport=dstport, net=chain, timeout_factor=1
        )()
        attacker.wait_until(lambda: attacker.is_connected, check_connected=False)

        self.helper_peer = attacker
        # We need to wait for the initial getheaders from the peer before we
        # start populating our blockstore. If we don't, then we may run ahead
        # to the next subtest before we receive the getheaders. We'd then send
        # an INV for the next block and receive two getheaders - one for the
        # IBD and one for the INV. We'd respond to both and could get
        # unexpectedly disconnected if the DoS score for that error is 50.
        # self.helper_peer.wait_for_getheaders(timeout=timeout)

    def reconnect_p2p(self, timeout=60):
        """Tear down and bootstrap the P2P connection to the node.

        The node gets disconnected several times in this test. This helper
        method reconnects the p2p and restarts the network thread."""
        self.nodes[0].disconnect_p2ps()
        self.bootstrap_p2p(timeout=timeout)

    def send_blocks(
        self,
        blocks,
        success=True,
        reject_reason=None,
        force_send=False,
        reconnect=False,
        timeout=960,
    ):
        """Sends blocks to test node. Syncs and verifies that tip has advanced to most recent block.

        Call with success = False if the tip shouldn't advance to the most recent block."""
        self.helper_peer.send_message(msg_block(block=blocks[0]))
        # self.helper_peer.send_blocks_and_test(
        #     blocks,
        #     self.nodes[0],
        #     success=success,
        #     reject_reason=reject_reason,
        #     force_send=force_send,
        #     timeout=timeout,
        #     expect_disconnect=reconnect,
        # )

        # if reconnect:
        #     self.reconnect_p2p(timeout=timeout)


def main():
    InvalidBlockTest().main()
