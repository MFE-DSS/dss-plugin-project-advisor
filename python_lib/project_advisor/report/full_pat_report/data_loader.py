# Data Loader
import dataiku
from datetime import datetime
import logging

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.tools import (build_user_to_project_mapping,
                                                          compute_project_scores_for_all_timestamps,
                                                          compute_project_scores_for_all_timestamps,
                                                          compute_project_scores_by_category,
                                                          compute_project_scores_by_category)


def load_pat_report_data(input_config):
    """
    Load data from the flow and run pre-computations.
    """
    logging.info("Loading Metrics & Checks Datasets and precomputing score")
    
    # INIT
    data = {}
    
    metric_dataset_name = input_config['metric_dataset']
    check_dataset_name = input_config['check_dataset']
    
    #client = configs["client"]
    project_categories = configs["project_categories"]
    instance_categories = configs["instance_categories"]
    metric_required_columns = configs["metric_required_columns"]
    check_required_columns = configs["check_required_columns"]
    
    
    # Load data from Flow
    metric_report = dataiku.Dataset(metric_dataset_name)
    metric_df = metric_report.get_dataframe()
    
    check_report = dataiku.Dataset(check_dataset_name)
    check_df = check_report.get_dataframe()
    
    # Check Report columns
    if not all(req_col in list(metric_df.columns) for req_col in metric_required_columns):
        raise Exception("The Metric report dataset doesn't have the correct schema, please provide a valid metric dataset")
    
    if not all(e in list(check_df.columns) for e in check_required_columns):
        raise Exception("The Check report dataset doesn't have the correct schema, please provide a valid check dataset")
    
    logging.info(f"Input Metric & Check Report datasets have the required schemas")
    
    is_instance_report = False
    if any(check_df["project_id"].isna()):
        is_instance_report = True
    
    logging.info(f"Webapp is running on instance report datasets : {is_instance_report}")
    
    # Format and compute dataset
    logging.info("Formatting metric and check datasets")
    check_df["timestamp"] = check_df["timestamp"].transform(lambda x : datetime.strptime(x, '%m/%d/%Y, %H:%M:%S'))
    metric_df["timestamp"] = metric_df["timestamp"].transform(lambda x : datetime.strptime(x, '%m/%d/%Y, %H:%M:%S'))
    
    # Precompute mapping tables
    logging.info("Precomputing user to project mapping")
    user_to_project_df = build_user_to_project_mapping()
    
    # Precompute dataframes to build the charts
    logging.info("Precomputing scores for project and instance checks")
    
    # Project Level pre-calculations.
    precomputed_result_project_df = compute_project_scores_for_all_timestamps(check_df, category=project_categories, group_by_project=True)
    precomputed_project_by_category_df = compute_project_scores_by_category(check_df, category=project_categories, group_by_project=True)
    
    # Instance Level pre-calcualations.
    precomputed_result_instance_df = None 
    precomputed_instance_by_category_df = None
    if is_instance_report:
        precomputed_result_instance_df = compute_project_scores_for_all_timestamps(check_df, category=instance_categories, group_by_project=False)
        precomputed_instance_by_category_df = compute_project_scores_by_category(check_df, category=instance_categories, group_by_project=False)
    
    data = {
        "is_instance_report" : is_instance_report,
        "user_to_project_df" : user_to_project_df,
        "check_df" : check_df,
        "metric_df" : metric_df,
        "precomputed_result_project_df" : precomputed_result_project_df,
        "precomputed_result_instance_df" : precomputed_result_instance_df,
        "precomputed_project_by_category_df" : precomputed_project_by_category_df, 
        "precomputed_instance_by_category_df" : precomputed_instance_by_category_df
    }
    logging.info("All data is loaded and precomputed!")
    return data