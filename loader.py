import logging
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL
logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)

def get_high_water_mark(coin_id: str):
    query = text("""
        select max(date)
        from staging.fact_price
        where coin_id = :coin_id
    """)
    with engine.connect() as connection:

        result = connection.execute(
            query,
            {"coin_id": coin_id}
        ).scalar()
    return result

def upsert_coin(
    coin_id: str,
    symbol: str,
    name: str  ):
    query = text("""
        insert into staging.dim_coin (
            coin_id,
            symbol,
            name )
        values (
            :coin_id,
            :symbol,
            :name  )
        on conflict (coin_id)
        do update set
            symbol = EXCLUDED.symbol,
            name = EXCLUDED.name
    """)
    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "coin_id": coin_id,
                "symbol": symbol,
                "name": name
            }
        )

def upsert_price_data(
    df: pd.DataFrame ):
    if df.empty:
        logger.info("Yüklənəcək data yoxdur.")
        return

    query = text("""
        insert into staging.fact_price (
            coin_id,
            date,
            price,
            market_cap,
            volume
        )
        values (
            :coin_id,
            :date,
            :price,
            :market_cap,
            :volume
        )
        on conflict (coin_id, date)
        do update set
            price = EXCLUDED.price,
            market_cap = EXCLUDED.market_cap,
            volume = EXCLUDED.volume
    """)
    with engine.begin() as connection:

        for _, row in df.iterrows():

            connection.execute(
                query,
                {
                    "coin_id": row["coin_id"],
                    "date": row["date"],
                    "price": row["price"],
                    "market_cap": row["market_cap"],
                    "volume": row["volume"]
                }
            )

    logger.info(
        f"{len(df)} sətir staging.fact_price "
        f"cədvəlinə yazıldı."
    )


def load_current_snapshot( df: pd.DataFrame ): 

    if df.empty:
        logger.info("Current snapshot boşdur.")
        return
    for _, row in df.iterrows():

        upsert_coin(
            coin_id=row["coin_id"],
            symbol=row["symbol"],
            name=row["name"]
        )

    price_df = df[
        [ "coin_id",
            "date",
            "price",
            "market_cap",
            "volume"  ]].copy()

    upsert_price_data(price_df)
    
    
    
def load_historical_data(
    df: pd.DataFrame
):
    if df.empty:
        logger.info("Historical data yoxdur.")
        return
    upsert_price_data(df)
    
    
    
def load_quarantine_data(df: pd.DataFrame):
    if df.empty:
        logger.info("Quarantine-a yazılacaq data yoxdur.")
        return

    query = text("""
        insert into staging.quarantine (
            coin_id,
            date,
            price,
            market_cap,
            volume,
            reason
        )
        values (
            :coin_id,
            :date,
            :price,
            :market_cap,
            :volume,
            :reason
        )
    """)

    with engine.begin() as connection:
        for _, row in df.iterrows():
            connection.execute(
                query,
                {
                    "coin_id": row["coin_id"],
                    "date": row["date"],
                    "price": row["price"],
                    "market_cap": row["market_cap"],
                    "volume": row["volume"],
                    "reason": row["reason"]
                }
            )

    logger.warning( f"{len(df)} sətir staging.quarantine "
        f"cədvəlinə yazıldı."
        )