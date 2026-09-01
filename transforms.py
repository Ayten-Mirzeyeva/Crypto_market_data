import pandas as pd

def daily_returns(df):

    if df.empty:
        result = df.copy()
        result["return"] = pd.Series(dtype="float64")
        return result

    result = df.copy()

    result["date"] = pd.to_datetime(result["date"])

    result = result.sort_values(
        ["coin_id", "date"]
    ).reset_index(drop=True)

    result["return"] = (
        result.groupby("coin_id")["price"]
        .pct_change()
    )

    return result


def moving_average(df, window=7):

    if window <= 0:
        raise ValueError("window must be greater than 0")

    if df.empty:
        result = df.copy()
        result["moving_average"] = pd.Series(dtype="float64")
        return result

    result = df.copy()

    result["date"] = pd.to_datetime(result["date"])

    result = result.sort_values(
        ["coin_id", "date"]
    ).reset_index(drop=True)

    result["moving_average"] = (
        result.groupby("coin_id")["price"]
        .transform(
            lambda x: x.rolling(
                window=window,
                min_periods=window
            ).mean()
        )
    )

    return result


def detect_gaps(df):

    if df.empty:
        return pd.DataFrame(
            columns=["coin_id", "missing_date"]
        )

    result = df.copy()

    result["date"] = pd.to_datetime(result["date"])

    gaps = []

    for coin_id, group in result.groupby("coin_id"):

        dates = (
            group["date"]
            .drop_duplicates()
            .sort_values()
        )

        if len(dates) < 2:
            continue

        expected_dates = pd.date_range(
            start=dates.min(),
            end=dates.max(),
            freq="D"
        )

        missing_dates = expected_dates.difference(dates)

        for missing_date in missing_dates:
            gaps.append(
                {
                    "coin_id": coin_id,
                    "missing_date": missing_date
                }
            )

    return pd.DataFrame(gaps)