import os
import sys
from pathlib import Path
from unknownlib.evm.fastw3 import FastW3
from unknownlib.evm.enums import Chain
from unknownlib.io import load_json

w3 = FastW3()
os.environ["INFURA_API_KEY"] = load_json((Path(__file__).parent / ".private/infura_api_key.json").absolute())
w3.init_web3(provider="infura", chain=Chain.GOERLI)
w3.init_ens(provider="infura", chain=Chain.ETHEREUM)
priv_key = '0x' + 'a' * 64
w3.init_acct(private_key=priv_key)