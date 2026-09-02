# Crypto Market Data Pipeline

An automated data pipeline that collects cryptocurrency market data from the CoinGecko API, validates and stores the data in PostgreSQL, transforms it into analytical marts, and visualizes the results in Power BI.

## Project Overview

The main goal of this project is to build a simple end-to-end data pipeline for cryptocurrency market data.

The pipeline performs the following steps:

1. Extract data from CoinGecko API
2. Validate incoming data
3. Load data into PostgreSQL
4. Create analytical SQL marts
5. Run the pipeline automatically with Prefect
6. Visualize the results in Power BI

## Architecture

```text
CoinGecko API
      ↓
    Raw Data
      ↓
   Validation
      ↓
   PostgreSQL
      ↓
   Staging
      ↓
     Marts
      ↓
   Power BI
```

## Technologies

* Python
* Pandas
* Requests
* Pandera
* PostgreSQL
* SQLAlchemy
* Prefect
* Pytest
* Power BI

## Data Pipeline

### 1. Data Ingestion

Cryptocurrency market data is collected from the CoinGecko API.

The pipeline collects information such as:

* Coin ID
* Symbol
* Name
* Price
* Market Cap
* Volume
* Date

The ingestion process also includes retry handling for temporary API failures.

### 2. Data Validation

Incoming data is validated using Pandera.

The validation checks include:

* Expected columns and data types
* Missing values
* Price greater than 0
* Volume greater than or equal to 0
* Market cap greater than or equal to 0
* Duplicate `(coin_id, date)` records
* Missing dates
* Price changes greater than ±50%

Suspicious records are sent to a quarantine table instead of being silently removed.

A DQ report is also generated for each pipeline run.

### 3. Incremental Loading

The pipeline uses a High-Water Mark approach.

Before fetching new historical data, the pipeline checks the latest date already stored in PostgreSQL for each coin.

This prevents unnecessary data requests and allows the pipeline to load only missing data.

The database uses UPSERT logic to prevent duplicate records when the pipeline is executed multiple times.

### 4. SQL Transformation

The `mart` schema contains analysis-ready views:

* Daily returns
* 7-day moving average
* 30-day moving average
* 30-day rolling volatility
* Maximum drawdown
* Volatility ranking

These views are created using SQL window functions.

### 5. Prefect Orchestration

The pipeline is orchestrated using Prefect.

The flow is divided into:

```text
Extract → Validate → Load → Transform → Report
```

The extraction task includes retries for temporary API failures.

The flow is scheduled to run daily.

## Data Quality

Each pipeline run generates a DQ report containing:

* Rows received
* Rows passed
* Rows quarantined
* Gaps found

A separate `demo_bad_data.py` script is included to test the validation rules using intentionally incorrect data.

## Testing

Unit tests are written using Pytest for the transformation functions.

Tests cover both normal and edge cases.

Run all tests with:

```bash
pytest -q
```

The tests do not require an internet connection or a running database.

## Power BI Dashboard

The final report contains:

* Cryptocurrency price trends
* 7-day and 30-day moving averages
* Volatility ranking
* Best 30-day return
* Worst 30-day return


## Project Structure

```text
Crypto Market/
│
├── ingestion.py
├── validation.py
├── loader.py
├── transforms.py
├── flow.py
├── run_pipeline.py
│
├── config.py
├── config.yaml
├── requirements.txt
├── .env.example
├── .gitignore
│
├── demo_bad_data.py
├── dq_report.txt
│
├── test/
│   └── test_transforms.py
│
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <https://github.com/Ayten-Mirzeyeva/Crypto_market_data.git>
cd Crypto-Market
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`.

Add your API and PostgreSQL connection settings.

### 5. Run the pipeline manually

```bash
python run_pipeline.py
```

### 6. Run tests

```bash
pytest -q
```

## Manual Testing

The pipeline can be tested for idempotency by running it twice and comparing the row count in `staging.fact_price`.

```sql
SELECT COUNT(*)
FROM staging.fact_price;
```

The row count should remain unchanged when there is no new data to load.

## Project Goal

This project demonstrates an end-to-end data workflow including API data ingestion, data validation, incremental loading, SQL transformations, workflow orchestration, testing, and data visualization.

````