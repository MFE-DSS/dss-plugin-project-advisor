# Configs
import dataiku

configs = {
    # Define local client
    "client" : dataiku.api_client(),
    
    # Columns in metric and check dataset
    "metric_required_columns" : ['timestamp', 'metric_name', 'metric_value', 'metric_type', 'project_id', 'result_data'],
    "check_required_columns" : ['timestamp', 'check_name', 'check_category', 'project_id', 'pass', 'message', 'result_data'],
    
    # List categories
    "project_categories" : ["AUTOMATION", "CODE", "DEPLOYMENT", "DOCUMENTATION", "FLOW", "PERFORMANCE", "ROBUSTNESS", "API_SERVICE"],
    "instance_categories" : ["PLATFORM", "USAGE", "PROCESSES", "CONFIGURATION"]
    
}
