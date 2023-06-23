import os
import sys
import unittest
from unknownlib.evm.core.base import (
    Web3Connector, ContractBook, ERC20ContractBook,
    ERC20, Chain)


class TestBaseMethods(unittest.TestCase):

    def test_web3_connector(self):
        chain = Chain.ARBITRUM
        w3 = Web3Connector()
        w3.init_web3(provider="infura", chain=chain)
        self.assertTrue(w3.web3.is_connected())
        self.assertEqual(chain, w3.chain)
        self.assertEqual(w3.eth.get_block(104165057)["timestamp"], 1687539576)
    
    def test_contract_book(self):
        book = ContractBook()
        chain = Chain.ARBITRUM
        book.init_web3(provider="infura", chain=chain)
        book.init_contract(
            addr="0xb87a436B93fFE9D75c5cFA7bAcFff96430b09868",
            abi="[]", key="gmx")
    
    def test_erc20_contract_book(self):
        book = ERC20ContractBook()
        chain = Chain.ARBITRUM
        book.init_web3(provider="infura", chain=chain)
        self.assertTrue(
            book.get_balance_of(token=ERC20.ARBITRUM_WETH, addr="0xE5d4924413ae59AE717358526bbe11BB4A5D76b9") >= 0)


if __name__ == '__main__':
    unittest.main()