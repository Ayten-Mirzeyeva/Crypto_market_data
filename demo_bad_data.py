from ingestion import run_ingestion
import pandas as pd
import logging
import numpy as np
from validation import current_schema
from config import CONFIG
from loader import (
    get_high_water_mark,
    load_current_snapshot,
    load_historical_data,
    load_quarantine_data
)
import pandera.pandas as pa
from pandera.errors import SchemaErrors


bad_data = pd.DataFrame(
    {
        "coin_id": ['bitcoin'],
        "price": [-50],
        'symbol':['btb'],
        'date' : ['today'],
        'volume': [200000],
        'market_cap':[ 100000],
        'name' : ['Bitcoin']
    }
)
print('Bad data:')
print(bad_data)

try:
    current_schema.validate(bad_data,
                            lazy= True)
    
    print('Data validdir!')
    
except pa.errors.SchemaError as exc:
    print('Data Rejected!')
    print('Data invaliddir!')
    print(exc)
    print(exc.failure_cases)
