import logging
import pandas as pd
import pandera.pandas as pa
from pandera import DataFrameSchema, Column, Check
from pandera.errors import SchemaErrors

logger = logging.getLogger(__name__)

current_schema = pa.DataFrameSchema(
    {
        "coin_id": Column(
            str,
            nullable=False
        ),

        "price": Column(
            float,
            Check.gt(0),
            nullable=False
        ),

        "symbol": Column(
            str,
            nullable=False
        ),

        "date": Column(
            pa.Date,
            nullable=False
        ),

        "volume": Column(
            float,
            Check.ge(0),
            nullable=True
        ),

        "market_cap": Column(
            float,
            Check.ge(0),
            nullable=True
        ),

        "name": Column(
            str,
            nullable=False
        )
    },
    report_duplicates="all",
    coerce=True,
    strict=True
)

historical_schema = pa.DataFrameSchema(
    {
        "coin_id": Column(
            str,
            nullable=False
        ),

        "price": Column(
            float,
            Check.gt(0),
            nullable=False
        ),

        "date": Column(
            pa.Date,
            nullable=False
        ),

        "volume": Column(
            float,
            Check.ge(0),
            nullable=True
        ),

        "market_cap": Column(
            float,
            Check.ge(0),
            nullable=True
        )
    },
    report_duplicates="all",
    coerce=True,
    strict=True
)


def check_duplicates(df):

    duplicates = df[
        df.duplicated(
            subset=["coin_id", "date"],
            keep=False
        )
    ]
    return duplicates


def detect_gaps(df):

    gaps = []
    for coin_id, coin_df in df.groupby("coin_id"):

        min_date = coin_df["date"].min()
        max_date = coin_df["date"].max()

        expected_dates = pd.date_range(
            start=min_date,
            end=max_date
        ).date

        existing_dates = coin_df["date"]

        missing_dates = expected_dates[~pd.Series(expected_dates).isin(existing_dates)]

        for missing_date in missing_dates:
            gaps.append({
                "coin_id": coin_id,
                "missing_date": missing_date
            })
    return pd.DataFrame(gaps)


def detect_anomaly(df):

    sorted_df = df.sort_values(
        ["coin_id", "date"]
    )

    change = (sorted_df.groupby("coin_id")["price"].pct_change())

    anomaly_mask = change.abs() > 0.5
    anomaly_df = sorted_df[anomaly_mask].copy()

    anomaly_df["reason"] = ("Day-over-day price change > 50%" )

    return anomaly_df


def validate_data(df, data_type):

    if df.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame()
        )

    if data_type == "current":
        schema = current_schema
    elif data_type == "historical":
        schema = historical_schema
    else:
        raise ValueError("data_type 'current' və ya 'historical' olmalıdır.")

    schema_failures = pd.DataFrame()
    try:
        validated_df = schema.validate(df, lazy=True)
    except SchemaErrors as exc:
        failure_cases = exc.failure_cases
        bad_indices = pd.Series(failure_cases["index"]).dropna().unique()
        schema_failures = df.loc[df.index.isin(bad_indices)].copy()
        schema_failures["reason"] = "Schema validation failed: " + failure_cases["check"].astype(str).iloc[0] if not failure_cases.empty else "Schema validation failed"

        logger.warning(
            f"{len(schema_failures)} sətir schema validasiyasından keçmədi "
            f"və quarantine-ə göndərildi."
        )

        remaining_df = df.loc[~df.index.isin(bad_indices)].copy()
        if remaining_df.empty:
            validated_df = remaining_df
        else:
            validated_df = schema.validate(remaining_df, lazy=True)

    duplicates = check_duplicates(validated_df)

    gaps = detect_gaps(validated_df)

    anomalies = detect_anomaly(validated_df)

    valid_df = validated_df[~validated_df.index.isin(anomalies.index)].copy()

    if not schema_failures.empty:
        anomalies = pd.concat([anomalies, schema_failures], ignore_index=True)

    if not duplicates.empty:
        logger.warning(f"{len(duplicates)} duplicate sətir tapıldı.")

    if not gaps.empty:
        logger.warning(f"{len(gaps)} gap tapıldı.")

    if not anomalies.empty:
        logger.warning(f"{len(anomalies)} anomaly tapıldı.")

    return valid_df, anomalies, duplicates, gaps
