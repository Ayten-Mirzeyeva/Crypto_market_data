import pandas as py
import logging
from prefect.logging import get_run_logger
from prefect import flow,task


def daily_returns(df):
    df = df.sort_values(['coin_id','date']).copy()
    df['return'] = df.groupby('coin_id')['price'].pct_change()
    return df
