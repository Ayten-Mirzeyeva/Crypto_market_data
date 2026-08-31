from ingestion import run_ingestion
from validation import validate_data
from loader import (
    get_high_water_mark,
    load_current_snapshot,
    load_historical_data,
    load_quarantine_data
)
from config import CONFIG
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging

high_water_marks = {}

for coin_id in CONFIG["tracked_coins"]:
    high_water_marks[coin_id] = get_high_water_mark(coin_id)

result = run_ingestion(high_water_marks)

current_df = result["current"]
historical_df = result["historical"]


if not current_df.empty:
    (   valid_current,
        anomalies_current,
        duplicates_current,
        gaps_current
    ) = validate_data(current_df, "current")

    load_current_snapshot(valid_current)
    load_quarantine_data(anomalies_current)

valid_history = pd.DataFrame()
anomalies_history = pd.DataFrame()
duplicates_history = pd.DataFrame()
gaps_history = pd.DataFrame()

if not historical_df.empty:
    (   valid_history,
        anomalies_history,
        duplicates_history,
        gaps_history
    ) = validate_data(historical_df,"historical")

    load_historical_data(valid_history)
    load_quarantine_data(anomalies_history)
    
    

report_dir = Path("data/dq_reports")
report_dir.mkdir(parents=True, exist_ok=True)

report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = report_dir / f"dq_report_{report_time}.txt"

rows_received = len(current_df)+ len(historical_df)

rows_passed = len(valid_history)+ len(valid_current)

rows_quarantined = len(anomalies_current)+ len(anomalies_history)

gaps_found = len(gaps_current) + len(gaps_history)

    
with open(report_file, "w", encoding="utf-8") as file:
    file.write("\nDATA QUALITY REPORT\n")
    file.write(f"Rows received: {rows_received}\n")
    file.write(f"Rows passed: {rows_passed}\n")
    file.write(f"Rows quarantined: {rows_quarantined}\n")
    file.write(f"Gaps found: {gaps_found}\n") 
    
    logging.info(f'DQ Report yaradıldı! ')

