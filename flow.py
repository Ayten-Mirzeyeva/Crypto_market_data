import pandas as pd
from prefect import flow, task
import logging
from loader import (
    get_high_water_mark,
    load_current_snapshot,
    load_historical_data,
    load_quarantine_data,
    check_mart_views
    )
from config import CONFIG
from pathlib import Path
from datetime import datetime
import numpy as np
import time
from prefect.task_runners import ThreadPoolTaskRunner, ProcessPoolTaskRunner
from validation import validate_data
from ingestion import run_ingestion

logger = logging.getLogger(__name__)

@task(
    name="Extract",
    retries=3,
    retry_delay_seconds=10
)
def extract_task():

    logging.info("EXTRACT START")

    high_water_marks = {}

    for coin_id in CONFIG["tracked_coins"]:
        high_water_marks[coin_id] = get_high_water_mark(coin_id)

    result = run_ingestion(high_water_marks)

    logging.info(
        f"Extract completed. "
        f"Current rows: {len(result['current'])}, "
        f"Historical rows: {len(result['historical'])}"
    )

    return result


@task(
    name = 'Validate',
    retries=3, 
    retry_delay_seconds=10
)
def validate_task(data):
    
    logging.info('VALIDATE START')
    
    current_df = data['current']
    historical_df = data['historical']
    
    valid_current = pd.DataFrame()
    anomalies_current = pd.DataFrame()
    duplicates_current = pd.DataFrame()
    gaps_current = pd.DataFrame()
    
    
    if not current_df.empty:
        (
            valid_current,
            anomalies_current,
            duplicates_current,
            gaps_current
        ) = validate_data(
            current_df,
            'current'
        )
    
    valid_history = pd.DataFrame()
    anomalies_history = pd.DataFrame()
    duplicates_history = pd.DataFrame()
    gaps_history = pd.DataFrame()
    
    if not historical_df.empty:
        (
            valid_history,
            anomalies_history,
            duplicates_history,
            gaps_history
        ) = validate_data(
            historical_df,
            'historical'
        )
    
    logging.info(
        f'Validate completed'
    )
    
    return {
        'valid_current': valid_current,
        'anomalies_current': anomalies_current,
        'duplicates_current': duplicates_current,
        'gaps_current': gaps_current,
        
        'valid_history': valid_history,
        'anomalies_history': anomalies_history,
        'duplicates_history': duplicates_history,
        'gaps_history': gaps_history
    }
    
    
@task(
    name= 'Load',
    retries = 3,
    retry_delay_seconds=10
)
def load_task(data):
    
    logging.info('LOAD START')
    
    
    if not data['valid_current'].empty:
        load_current_snapshot(
            data['valid_current']
        )
        
    if not data['valid_history'].empty:
        load_historical_data(
            data['valid_history']
        )
        
    if not data['anomalies_current'].empty:
        load_quarantine_data(
            data['anomalies_current']
        )
    
    if not data['anomalies_history'].empty:
        load_quarantine_data(
            data['anomalies_history']
        )
        
    logging.info('Load completed.')  
    
    return True
    
    
@task(
    name="Transform",
    retries=3,
    retry_delay_seconds=10
)
def transform_task():

    logging.info("TRANSFORM START")

    check_mart_views()

    logging.info("Transform completed.")

    return True


@task(
    name="Report",
    retries=3,
    retry_delay_seconds=10
)
def report_task(data):

    logging.info("REPORT START")

    report_dir = Path("data/dq_reports")

    report_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    report_time = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report_file = (
        report_dir /
        f"dq_report_{report_time}.txt"
    )

    rows_received = (
        len(data["valid_current"])
        + len(data["anomalies_current"])
        + len(data["valid_history"])
        + len(data["anomalies_history"])
    )

    rows_passed = (
        len(data["valid_current"])
        + len(data["valid_history"])
    )

    rows_quarantined = (
        len(data["anomalies_current"])
        + len(data["anomalies_history"])
    )

    gaps_found = (
        len(data["gaps_current"])
        + len(data["gaps_history"])
    )

    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "DATA QUALITY REPORT\n"
        )
        file.write(
            "===================\n"
        )
        file.write(
            f"Rows Received: {rows_received}\n"
        )
        file.write(
            f"Rows Passed: {rows_passed}\n"
        )
        file.write(
            f"Rows Quarantined: {rows_quarantined}\n"
        )
        file.write(
            f"Gaps Found: {gaps_found}\n"
        )

    logging.info(
        f"Report completed: {report_file}"
    )

    return str(report_file)
    
    
@flow(name="CRYPTO MARKET DATA PIPELINE")
def crypto_pipeline():

    extracted_data = extract_task()

    validated_data = validate_task(
        extracted_data
    )

    load_task(
        validated_data
    )

    transform_task()

    report_task(
        validated_data
    )

    return True
    
if __name__ == "__main__":
    crypto_pipeline()