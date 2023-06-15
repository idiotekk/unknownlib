"""
This example fetch trade price from uniswap v3 USDC pool,
then plot the prices in a interactive chart.
"""
import os
import pandas as pd
import numpy as np
from unknownlib.evm.fastw3 import FastW3, Chain
from unknownlib.plt.bk import plot


if __name__ == "__main__":

    fw = FastW3()
    fw.init_web3(provider="infura", chain=Chain.ETHEREUM)
    fw.init_scan(chain=Chain.ETHEREUM)
    fw.init_contract(addr="0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
                    abi=fw.get_abi(addr="0x8f8ef111b67c04eb1641f5ff19ee54cda062f163"),
                    label="uniswap_v3_usdc3")

    tz = "US/Eastern"
    sdate = 20230613
    edate = 20230614
    start_time = pd.to_datetime("20230613").tz_localize("US/Eastern")
    end_time = pd.to_datetime("20230614").tz_localize("US/Eastern")
    start_block_number = fw._scan.get_block_number_by_timestamp(int(start_time.value / 1e9))
    end_block_number = fw._scan.get_block_number_by_timestamp(int(end_time.value / 1e9)) 

    logs = fw.get_event_logs(
        contract="uniswap_v3_usdc3",
        event_name="Swap",
        from_block=start_block_number,
        to_block=end_block_number,
    )

    df = pd.DataFrame([{**_["args"], **{k: _[k] for k in ["blockNumber"]}} for _ in logs])
    df["price"] = - df["amount0"] / df["amount1"] * 1e18 / 1e6
    df["side"] = np.where( df["amount0"] > 0, "buy", "sell")
    df["timestamp"] = start_time + (end_time - start_time) * ( df["blockNumber"] - start_block_number) / (end_block_number - start_block_number) 


    from unknownlib.plt.bk import tsplot
    from bokeh.plotting import output_file, save
    p = tsplot(df,
        time_var="timestamp",
        hue="side",
        line_types="circle",
        y="price",
        figsize=(1600, 1200),
        show=False)
    output_file(os.path.expandvars('$HOME/Desktop/plot.html'), mode='inline')
    save(p)