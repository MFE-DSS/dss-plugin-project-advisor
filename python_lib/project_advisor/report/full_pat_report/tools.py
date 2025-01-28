# Tools
import logging
import pandas as pd

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles

#########################
## User Auth functions ##
#########################

def user_is_admin(user_login):
    """
    Return user admin status
    """
    logging.info("Checking if user is admin")
    client = configs["client"]
    
    groups = client.list_groups()
    user = client.get_user(user_login)
    settings = user.get_settings()
    groups = settings.get_raw().get("groups",[])
    
    is_admin = False
    for group_name in groups:
        group = client.get_group(group_name)
        if group.get_definition().get("admin", False):
            is_admin = True
    return is_admin 

def build_user_to_project_mapping():
    """
    Building access to user to project mapping
    """
    logging.info("Building access to user to project mapping")
    client = configs["client"]
    users = client.list_users()
    groups = client.list_groups()
    projects = client.list_projects()

    # Enrich projects (precomputation)
    for p in projects:
        project_key = p["projectKey"]
        project = client.get_project(project_key)
        p.update({"permissions": project.get_permissions()["permissions"]})

    user_to_project_mapping = []
    for user in users:
        user_login = user["login"]
        user_groups = user["groups"]

        for p in projects:
            project_key = p["projectKey"]
            project_owner = p["ownerLogin"]

            is_project_owner = False
            is_shared_by_user = False
            is_shared_by_group = False
            
            if user_login == project_owner:
                is_project_owner = True
            
            else:
                for permission in p["permissions"]:
                    # If has at least write permissions on project.
                    if any([permission['admin'],
                           permission['writeProjectContent']]):

                        if permission.get("user") == user_login:
                            is_shared_by_user = True

                        if permission.get("group") in user_groups:
                            is_shared_by_group = True

            if any([is_project_owner,is_shared_by_user, is_shared_by_group]):
                user_to_project_mapping.append({
                    "user_login" : user_login,
                    "project_key" : project_key,
                    "is_project_owner" : is_project_owner,
                    "is_shared_by_user" : is_shared_by_user,
                    "is_shared_by_group" : is_shared_by_group
                })
    return pd.DataFrame.from_dict(user_to_project_mapping)

def get_user_project_keys(user_login, mapping_df):
    return list(mapping_df[mapping_df["user_login"]==user_login]["project_key"])


###############################
## Dynamic Display Functions ##
###############################
def enrich_project_list(project_list):
    """
    Enrich project keys with project metadata.
    """
    logging.info("Enriching Projects")
    client = configs["client"]
    
    projects_all = client.list_projects()
    return [
        {
            project['projectKey']: {
                "name": project.get("name", "NO_NAME"),
                "owner": project.get("ownerDisplayName", "UNKNOWN_OWNER"),
                "project_type": project.get("projectType", "UNKNOWN_PROJECT_TYPE")
            }
        }
        for project in projects_all if project['projectKey'] in project_list
    ]

###############################
## Precomputations functions ##
###############################
def compute_project_scores_for_all_timestamps(df, category=None, group_by_project=True):
    """
    Compute Project Score over time.
    """
    logging.info(f"Compute Project Score over time, group_by_project : {group_by_project}")
    # If category list specified, filter the dataframe by category first
    if category:
        df = df[df["check_category"].isin(category)]

    # Define grouping columns based on the input parameter and group the dataframe
    grouping_cols = ['timestamp'] + (['project_id'] if group_by_project else [])
    grouped = df.groupby(grouping_cols)
    
    results = []
    for group_keys, group in grouped:
        # Count the number of passed checks (True) and failed checks (False)
        value_counts = group["pass"].value_counts()

        # Handle cases where True or False may not exist in the column
        passed_checks = value_counts.get(True, 0)
        failed_checks = value_counts.get(False, 0)

        # Avoid division by zero
        total_checks = passed_checks + failed_checks
        project_score = round(passed_checks / total_checks, 2) * 100 if total_checks > 0 else 0.0

        # Create result dictionary with keys based on grouping
        if len(grouping_cols) == 1:
            timestamp = group_keys
        else:
            timestamp = group_keys[0]
        
        # Create result dictionary with keys based on grouping
        result_dict = {
            'timestamp': timestamp,
            'project_score': round(project_score,2)
        }
        
        if group_by_project:
            result_dict['project_id'] = group_keys[1]

        results.append(result_dict)

    result_df = pd.DataFrame(results)
    
    result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])

    # Sort the DataFrame by the appropriate columns
    sort_columns = ['timestamp'] + (['project_id'] if group_by_project else [])
    result_df = result_df.sort_values(by=sort_columns)

    # Compute the delta (difference) in project score
    if group_by_project:
        result_df['delta'] = result_df.groupby('project_id')['project_score'].diff()
    else:
        result_df['delta'] = result_df['project_score'].diff()

    return result_df


def compute_project_scores_by_category(df, category=None, group_by_project=True):
    """
    Compute Project Scores by Category
    If category list specified, filter the dataframe by category first
    """
    logging.info(f"Compute Project Score by category, group_by_project : {group_by_project}")
    
    if category:
        df = df[df["check_category"].isin(category)]
    
    # Define grouping columns based on the input parameter and group the dataframe
    grouping_cols = ['timestamp', 'check_category'] + (['project_id'] if group_by_project else [])
    grouped = df.groupby(grouping_cols)

    results = []
    for group_keys, group in grouped:
        # Count the number of passed (True) and failed (False) checks
        value_counts = group["pass"].value_counts()

        # Retrieve counts or default to 0
        passed_checks = value_counts.get(True, 0)
        failed_checks = value_counts.get(False, 0)

        total_checks = passed_checks + failed_checks
        
        # Compute the project score (0% if no checks, otherwise the ratio of passed checks)
        if total_checks == 0:
            project_score = 0.0
        else:
            project_score = round(passed_checks / total_checks * 100, 2)

        result_dict = {
            'timestamp': group_keys[0],
            'project_score': project_score,
            'category': group_keys[1]
        }
        
        if group_by_project:
            result_dict['project_id'] = group_keys[2]
        
        results.append(result_dict)

    result_df = pd.DataFrame(results)

    # Extract the date from the timestamp and convert it to datetime format
    result_df['date'] = pd.to_datetime(result_df['timestamp'])

    # Filter by the specified project categories
    result_df = result_df[result_df['category'].isin(category)]
    
    # Create a new column for bar colors based on project score
    def get_color(score):
        if score > 70:
            return '#b8e7ba'
        elif 50 <= score <= 70:
            return '#fce9a5'
        else:
            return '#fcd1b9'

    result_df['color'] = result_df['project_score'].apply(get_color)
    
    return result_df


def compute_fail_to_pass_df(df, category=None):
    """
    Compute Fail to pass df
    """
    logging.info(f" Compute Fail to pass df")
    
    # Check that there are at least two distinct timestamps
    if df["timestamp"].nunique() <= 1:
        return pd.DataFrame()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if category:
        df = df[df["check_category"].isin(category)]

    df = df.sort_values(by='timestamp')

    # Get the two most recent unique timestamps
    last_two_timestamps = df['timestamp'].drop_duplicates().nlargest(2)

    # Extract the rows corresponding to these two timestamps
    most_recent_df = df[df['timestamp'] == last_two_timestamps.iloc[0]]
    previous_df = df[df['timestamp'] == last_two_timestamps.iloc[1]]

    # Merge the two dataframes to compare the 'pass' status (left merge)
    comparison_df = previous_df[['check_name', 'pass']].merge(
        most_recent_df[['check_name', 'pass']], 
        on='check_name', 
        suffixes=('_previous', '_recent'),
        how='left'
    )

    # Identify the checks that changed from fail (False) to pass (True)
    changed_to_pass = comparison_df[(comparison_df['pass_previous'] == False) & (comparison_df['pass_recent'] == True)]
    changed_to_pass['status_change'] = 'Fail to Pass'

    return changed_to_pass


def compute_check_reco_table_df(df, category=None):
    """
    Compute Check reco Table df
    """
    logging.info(f" Compute Fail to pass df")
    
    if category:
        df = df[df["check_category"].isin(category)]

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    most_recent_timestamp = df['timestamp'].max()
    most_recent_rows = df[df['timestamp'] == most_recent_timestamp]

    # Create a new column 'status' that marks whether the check passed or failed
    most_recent_rows['status'] = most_recent_rows['pass'].apply(lambda x: 'Pass' if x else 'Fail')
    return most_recent_rows


def compute_metric_df(df_metric, instance=True):
    """
    Compute Check reco Table df
    """
    logging.info(f"Compute Fail to pass df, instance : {instance}")
    
    if instance:
        df_metric = df_metric[df_metric["project_id"].isna()]

    return df_metric
