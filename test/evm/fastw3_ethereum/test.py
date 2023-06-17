import os
import sys
import unittest
import random
from pprint import pformat
from pathlib import Path
from unknownlib.evm.fastw3 import FastW3
from unknownlib.evm.enums import Chain
from unknownlib.io import load_json
from unknownlib import log

def _fectch_key(path):
    return load_json((Path(__file__).parent / "../.private"/ path).absolute())
 
w3 = FastW3()
os.environ["INFURA_API_KEY"] = _fectch_key("infura_api_key.json")
w3.init_web3(provider="infura", chain=Chain.ETHEREUM)
w3.init_ens(provider="infura", chain=Chain.ETHEREUM)
w3.init_scan(chain=Chain.ETHEREUM)
priv_key = _fectch_key("test_private_key.json") # 0x4cb32d187373a8a5B8B976923227d648e33e4d4a
w3.init_acct(private_key=priv_key)
friend_addr = "0xE5d4924413ae59AE717358526bbe11BB4A5D76b9"


class TestFastW3Methods(unittest.TestCase):

    def test_contract(self):

        contract_name = "ENS public resolver"
        w3.init_contract(
            addr="0x231b0ee14048e9dccd1d247744d114a4eb5e8e63",
            label=contract_name)
        logs = w3.get_event_logs(
            contract=contract_name,
            event_name="ContenthashChanged",
            from_block=17251695,
            to_block=17251695)
        log.info(pformat([dict(_) for _ in logs]))

    def test_ens(self):
        name_ = "vitalik.eth"
        addr = w3.ens.address(name_)
        log.info((name_, addr))
        self.assertEqual(name_, w3.ens.name(addr))


if __name__ == '__main__':
    unittest.main()