import pandas as pd
import logging
from transforms import daily_returns

def test_daily_returns_simple():
    df = pd.DataFrame({
        'coin_id': ['btc','btc','btc'],
        'date': ['2026-01-01', '2026-01-02', '2026-01-03'],
        'price':['100.0','99.1','110.0']
    }
    )
    out = daily_returns(df)
    assert out['return'].iloc[1] == 0.10
    assert out['return'].iloc[2] == -0.10
    assert pd.isna(out['return'].iloc[0])

    