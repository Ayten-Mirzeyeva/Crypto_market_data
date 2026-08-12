from datetime import date, datetime
import json
import logging
from pathlib import Path
import time

import pandas as pd
import requests

from config import API_KEY, CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ])
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://api.coingecko.com/api/v3"
HEADERS = {
    "x-cg-demo-api-key": API_KEY
} if API_KEY else {}

def safe_request(url: str, params: dict):
    retry_delays = [2, 4, 8]
    for attempt in range(len(retry_delays) + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=30 )
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429:
                if attempt < len(retry_delays):
                    wait = retry_delays[attempt]
                    logger.warning(
                        f"Rate limit (429). "
                        f"{wait} saniyə gözlənilir. "
                        f"Cəhd: {attempt + 1}"
                    )
                    time.sleep(wait)
                    continue
                logger.error(
                    "API rate limit problemi "
                    "Maksimum retry sayı keçildi.")
                response.raise_for_status()
                
            response.raise_for_status()
        except requests.RequestException as error:
            if attempt == len(retry_delays):
                logger.error(
                    f"API request xətası: {error}",
                    exc_info=True)
                raise
            wait = retry_delays[attempt]
            logger.warning(
                f"Request xətası: {error}. "
                f"{wait} saniyə sonra yenidən yoxlanılır."
            )
            time.sleep(wait)
    raise RuntimeError("API request uğursuz oldu.")

def save_raw_json(name: str, payload):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = RAW_DIR / f"{name}_{timestamp}.json"
    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2
        )
    logger.info( f"Raw data fayla yazıldı: {file_path}")

def fetch_market_snapshot():

    url = f"{API_URL}/coins/markets"
    params = {
        "vs_currency": CONFIG["target_currency"],
        "ids": ",".join(CONFIG["tracked_coins"])}
    logger.info("Current market snapshot çəkilir...")
    data = safe_request(url, params)
    if not data:
        logger.warning("Market snapshot boş qaytarıldı.")
        return pd.DataFrame()
    save_raw_json( "snapshot_markets",data)

    df = pd.DataFrame(data)
    df = df[[ "id",
            "symbol",
            "name",
            "current_price",
            "market_cap",
            "total_volume"  ]].copy()
    df.columns = [  "coin_id",
                    "symbol",
                    "name",
                    "price",
                    "market_cap",
                    "volume"]
    df["date"] = date.today()

    logger.info(
        f"Current snapshot: {len(df)} coin alındı.")
    return df

def fetch_historical_chart(
    coin_id: str,
    history_days: int,
    latest_date=None ):

    url = (
        f"{API_URL}/coins/"
        f"{coin_id}/market_chart"
    )
    params = {
        "vs_currency": CONFIG["target_currency"],
        "days": history_days
    }
    logger.info(
        f"{coin_id} üçün {history_days} günlük "
        f"historical data çəkilir..."
    )
    chart_data = safe_request(
        url,
        params
    )
    if not chart_data:
        logger.warning(
            f"{coin_id} üçün historical data boşdur."
        )
        return pd.DataFrame()

    save_raw_json(f"history_{coin_id}",chart_data)
    
    prices = pd.DataFrame(
        chart_data["prices"],
        columns=[
            "timestamp",
            "price"
        ]
    )
    market_caps = pd.DataFrame(
        chart_data["market_caps"],
        columns=[
            "timestamp",
            "market_cap"
        ]
    )
    volumes = pd.DataFrame(
        chart_data["total_volumes"],
        columns=[
            "timestamp",
            "volume"
        ])
    df = prices.merge(
        market_caps,
        on="timestamp",
        how="left")
    df = df.merge(
        volumes,
        on="timestamp",
        how="left")

    df["date"] = pd.to_datetime(
        df["timestamp"],
        unit="ms" ).dt.date

    df["coin_id"] = coin_id
    df = df[[ "coin_id",
            "date",
            "price",
            "market_cap",
            "volume" ]    ]
    
    
    df = (df.sort_values("date")
        .groupby(["coin_id", "date"],
        as_index=False ).last())

    if latest_date is not None:
        df = df[
            df["date"] > latest_date]
        
    logger.info(
        f"{coin_id}: {len(df)} yeni historical sətir.")
    return df

def fetch_all_historical_data(high_water_marks=None):

    all_data = []
    if high_water_marks is None:
        high_water_marks = {}

    for coin_id in CONFIG["tracked_coins"]:
        latest_date = high_water_marks.get(coin_id)
        logger.info(
            f"{coin_id} üçün high-water mark: "
            f"{latest_date}"
        )
        if latest_date is None:
            history_days = CONFIG["history_days"]
        else:
            history_days = (
                date.today() - latest_date
            ).days
            if history_days <= 0:

                logger.info(
                    f"{coin_id} üçün yeni historical "
                    f"data yoxdur."
                )
                continue
        df = fetch_historical_chart(
            coin_id,
            history_days,
            latest_date
        )
        if not df.empty:
            all_data.append(df)
        time.sleep(1)
    if not all_data:
        return pd.DataFrame()
    return pd.concat(
        all_data,
        ignore_index=True
    )
def run_ingestion(high_water_marks=None):

    logger.info("INGESTION START")

    current_df = fetch_market_snapshot()

    historical_df = fetch_all_historical_data(
        high_water_marks
    )

    logger.info("INGESTION SUCCESS")

    return {
        "current": current_df,
        "historical": historical_df
    }
    
if __name__ == "__main__":
    result = run_ingestion()

    print("\n CURRENT MARKET DATA ")
    print(result["current"].head())

    print("\n HISTORICAL DATA ")
    print(result["historical"].head())
    
