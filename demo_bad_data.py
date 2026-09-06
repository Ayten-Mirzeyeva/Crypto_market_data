import pandas as pd
from validation import current_schema
from pandera.errors import SchemaErrors

bad_data = pd.DataFrame(
    {
        "coin_id": ["bitcoin"],
        "price": [-50.0],
        "symbol": ["btc"],
        "date": [pd.Timestamp("2026-09-01").date()],
        "volume": [200000.0],
        "market_cap": [100000.0],
        "name": ["Bitcoin"],
    }
)

print("Bad data:")
print(bad_data)

try:
    current_schema.validate(bad_data, lazy=True)
    print("Data validdir!")
    
except SchemaErrors as exc:
    print("Data Rejected!")
    print("Data invaliddir!")
    print(exc.failure_cases)
