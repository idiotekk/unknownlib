import os
import sys
import unittest
import random
from pprint import pformat
from pathlib import Path
from unknownlib.evm.fastw3 import FastW3
from unknownlib.evm.core import Chain, ERC20
from unknownlib.io import load_json
from unknownlib import log

def _fectch_key(path):
    return load_json((Path(__file__).parent / "../.private"/ path).absolute())
 
chain = Chain.ARBITRUM
w3 = FastW3()
os.environ["INFURA_API_KEY"] = _fectch_key("infura_api_key.json")
w3.init_web3(provider="infura", chain=chain)


class TestFastW3Methods(unittest.TestCase):

    def test_price_feed(self):
        tokens = [
            ERC20.ARBITRUM_WBTC,
            ERC20.ARBITRUM_WETH,
        ]
        print({t: w3.get_latest_price(t) for t in tokens})


if __name__ == '__main__':
    unittest.main()