import dataiku
from datetime import datetime
import logging

def load_historical_metric_check_reports(instance_metric_report_name, instance_check_report_name):
    # Example: load a DSS dataset as a Pandas dataframe
    logging.info("Loading Metrics and Checks datasets")
    
    check_report = dataiku.Dataset(instance_check_report_name)
    check_df = check_report.get_dataframe()

    metric_report = dataiku.Dataset(instance_metric_report_name)
    metric_df = metric_report.get_dataframe()

    check_df["timestamp"] = check_df["timestamp"].transform(lambda x : datetime.strptime(x, '%m/%d/%Y, %H:%M:%S'))
    metric_df["timestamp"] = metric_df["timestamp"].transform(lambda x : datetime.strptime(x, '%m/%d/%Y, %H:%M:%S'))
    return metric_df, check_df