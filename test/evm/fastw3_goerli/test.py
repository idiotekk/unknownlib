import os
import sys
import unittest
import random
from pathlib import Path
from unknownlib.evm.fastw3 import FastW3
from unknownlib.evm.enums import Chain
from unknownlib.io import load_json
from unknownlib import log

def _fectch_key(path):
    return load_json((Path(__file__).parent / path).absolute())
 
w3 = FastW3()
os.environ["INFURA_API_KEY"] = _fectch_key(".private/infura_api_key.json")
w3.init_web3(provider="infura", chain=Chain.GOERLI)
priv_key = _fectch_key(".private/private_key.json") # 0x4cb32d187373a8a5B8B976923227d648e33e4d4a
w3.init_acct(private_key=priv_key)
friend_addr = "0xE5d4924413ae59AE717358526bbe11BB4A5D76b9"
   

class TestFastW3Methods(unittest.TestCase):

    def test_send_ether(self):
        balance_ = w3.eth.get_balance(w3.acct.address)
        log.info(f"balance before: {balance_}")
        w3.send_ether(to=friend_addr, value=0.000001, gas=21000)
        balance_ = w3.eth.get_balance(w3.acct.address)
        log.info(f"balance after: {balance_}")

    def test_contract(self):

        # check balance of coin
        token_name = "dummyCoin"
        w3.init_contract(
            addr="0xa2bd28f23A78Db41E49db7d7B64b6411123a8B85",
            abi=[
                {"constant":True,"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},
                {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},
                {"constant":True,"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"}
                ],
            label=token_name)
        balance_ = w3.contract(token_name).functions.balanceOf(w3.acct.address).call()
        log.info(f"balance of {token_name} = {balance_}")

        # change allowance
        allowance_before = w3.contract(token_name).functions.allowance(w3.acct.address, friend_addr).call()
        new_allowance = int(random.randint(2, 9) * 1e10)
        w3.call(w3.contract(token_name).functions.approve(friend_addr, new_allowance), gas=2100000,)
        allowance_after = w3.contract(token_name).functions.allowance(w3.acct.address, friend_addr).call()
        log.info((allowance_before, new_allowance, allowance_after))
        self.assertEqual(new_allowance, allowance_after)


if __name__ == '__main__':
    unittest.main()