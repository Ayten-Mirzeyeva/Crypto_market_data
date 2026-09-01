from prefect import serve
from flow import crypto_pipeline


if __name__ == "__main__":

    crypto_pipeline.serve(
        name="crypto-daily",
        cron="0 10 * * *",
        tags=["crypto", "daily"],
        description="Daily Crypto Market Data Pipeline"
    )
    
    