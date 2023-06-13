import os
from .enums import Chain
import requests


class ResponseParser:
    @staticmethod
    def parse(response: requests.Response):
        content = response.json()
        result = content["result"]
        if "status" in content.keys():
            status = bool(int(content["status"]))
            message = content["message"]
            assert status, f"{result} -- {message}"
        else:
            # GETH or Parity proxy msg format
            # TODO: see if we need those values
            jsonrpc = content["jsonrpc"]
            cid = int(content["id"])
        return result


class Etherscan:
    
    _api_key: str
    _base_url: str

    def __init__(self, chain: Chain) -> None:

        self._api_key = os.environ[{
            Chain.ETHEREUM: "ETHERSCAN_API_KEY",
            Chain.ARBITRUM: "ARBISCAN_API_KEY",
        }[chain]]
        self._base_url = {
            Chain.ETHEREUM: "https://api.etherscan.io/api?",
            Chain.ARBITRUM: "https://api.arbiscan.io/api?",
        }[chain]
        
    def get(self, **kw):
        url = self._base_url + "&".join([f"{k}={v}" for k, v in kw.items()])
        r = requests.get(url, headers={"User-Agent": ""})
        return ResponseParser.parse(r)
    
    def get_block_number_by_timestamp(self, timestamp: int) -> int:
        kw = dict(
            module = "block",
            action = "getblocknobytime",
            timestamp = timestamp,
            closest = "before",
            apikey = self._api_key,
        )
        return int(self.get(**kw))