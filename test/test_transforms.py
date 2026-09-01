import pandas as pd
import pytest

from transforms import (
    daily_returns,
    moving_average,
    detect_gaps
)

def test_daily_returns_normal():

    df = pd.DataFrame({
        "coin_id": ["btc", "btc", "btc"],
        "date": ["2026-01-01","2026-01-02","2026-01-03"],
        "price": [100.0, 110.0, 99.0 ]
    })

    result = daily_returns(df)
    assert pd.isna(result["return"].iloc[0])
    assert result["return"].iloc[1] == pytest.approx(0.10)
    assert result["return"].iloc[2] == pytest.approx(-0.10)


def test_daily_returns_empty():

    df = pd.DataFrame(columns=["coin_id", "date", "price"])

    result = daily_returns(df)
    assert result.empty
    assert "return" in result.columns


def test_moving_average_normal():

    df = pd.DataFrame({
        "coin_id": ["btc", "btc", "btc", "btc"],
        "date": [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
            "2026-01-04"
        ],
        "price": [
            10.0,
            20.0,
            30.0,
            40.0
        ]
    })

    result = moving_average( df, window=3)

    assert pd.isna(result["moving_average"].iloc[0])
    assert pd.isna(result["moving_average"].iloc[1])
    assert result["moving_average"].iloc[2] == pytest.approx(20.0)
    assert result["moving_average"].iloc[3] == pytest.approx(30.0)


def test_moving_average_empty():

    df = pd.DataFrame(
    columns=["coin_id", "date", "price"]
    )

    result = moving_average(df,window=7)

    assert result.empty
    assert "moving_average" in result.columns

def test_detect_gaps_normal():

    df = pd.DataFrame({
        "coin_id": ["btc", "btc"],
        "date": ["2026-01-01","2026-01-03"]
    })

    result = detect_gaps(df)
    assert len(result) == 1
    assert result.iloc[0]["coin_id"] == "btc"
    assert result.iloc[0]["missing_date"] == pd.Timestamp("2026-01-02")


def test_detect_gaps_empty():

    df = pd.DataFrame(columns=["coin_id", "date"])

    result = detect_gaps(df)
    assert result.empty
    assert list(result.columns) == ["coin_id","missing_date"]