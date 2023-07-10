"""
This example fetches logs of an event from a contract and write to sql database.
"""
import os
import requests
import argparse
import time
import json
import pandas as pd
from requests.adapters import HTTPAdapter
from hexbytes import HexBytes
from pprint import pprint
from unknownlib.evm.fastw3 import FastW3, Chain, log
from unknownlib.evm.core import ERC721ContractBook
from unknownlib.evm.timestamp import to_int
from unknownlib.evm.sql import SQLConnector
from unknownlib.dt import sleep
from typing import Tuple, List


class NFTGuru(FastW3, ERC721ContractBook):
    pass


w3 = NFTGuru()
sql = SQLConnector()
sess = requests.Session()
sess.mount('https://', HTTPAdapter(pool_connections=1))
sess.auth = (
    os.environ["INFURA_API_KEY"],
    os.environ["INFURA_API_KEY_SECRET"])


def get_token_metadata(contract_name: str, token_id: int, max_retries: int=5) -> dict:

    uri = w3.get_token_uri(contract_name, token_id)
    log.info(f"URI: {uri}")
    #r = sess.get(uri)
    contract_addr = w3.contract(contract_name).address

    retries = 0
    while retries < max_retries:
        retries += 1
        r = sess.get(f"https://nft.api.infura.io/networks/{w3.chain.value}/nfts/{contract_addr}/tokens/{token_id}")
        j = r.json()
        metadata = {k: json.dumps(j[k]) for k in j}
        if "status" in metadata:
            if metadata["status"] == "429":
                sleep("1s")
            else:
                raise ValueError("can't handle response: " + json.dumps(metadata))
        else:
            metadata["tokenId"] = token_id
            return metadata


if __name__ == "__main__":

    contract_book = {
        "MysteryBean": "0x3Af2A97414d1101E2107a70E7F33955da1346305",
        "AzukiElementals": "0xB6a37b5d14D502c3Ab0Ae6f3a0E058BC9517786e",
        "MAYC": "0x60E4d786628Fea6478F785A6d7e704777c86a7c6",
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("--name")
    parser.add_argument("--addr")
    parser.add_argument("--start-id", type=int, default=0)
    args = parser.parse_args()

    chain = Chain.ETHEREUM
    contract_name = args.name
    contract_addr = contract_book.get(args.name, None) or args.addr
    log.info(f"contract: {contract_name}, {contract_addr}")
    db_path = '/tmp/evm.db'

    w3.init_web3(provider="infura", chain=chain)
    w3.init_scan(chain=chain)
    w3.init_contract(addr=contract_addr, key=contract_name)
    sql.connect(db_path)

    table_name=f"nft_metadata_{contract_name}"
    if sql.table_exists(table_name):
        token_id_count = sql.read(f"SELECT tokenId FROM {table_name}")["tokenId"].value_counts()
        assert (token_id_count <= 1).all(), f"duplicate tokenId found: {token_id_count[token_id_count > 1]}"
        existing_token_id = list(token_id_count.values)
    else:
        existing_token_id = []

    max_id = w3.contract(contract_name).functions["totalSupply"]().call()
    failed_token_id_and_errors = {}
    for token_id in range(args.start_id, max_id + 1): # +1 to include `max_id`

        if token_id in existing_token_id:
            log.info(f"tokenId {token_id} was already downloaded. Skipping.")
            continue

        # fetch
        log.info(f"fetching metadata for {token_id}")
        def _fetch_single(token_id):
            metadata = get_token_metadata(contract_name, token_id)
            row = pd.DataFrame(metadata, index=[token_id])
            sql.write(row, table_name=table_name, index=["tokenId"])
        try:
            _fetch_single(token_id)
        except Exception as e:
            log.error(f"failed: {e}")
            raise e
            #failed_token_id_and_errors[token_id] = e