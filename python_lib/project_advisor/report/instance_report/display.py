import logging
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


from project_advisor.report.instance_report.data_loader import load_historical_metric_check_reports

from project_advisor.report.instance_report.components import (build_numerical_metric_card,
                                                               build_hist_card,
                                                               build_pie_chart_card,
                                                               build_instance_check_card,
                                                               build_project_check_card
                                                              )
from project_advisor.report.instance_report.style import ( ROW_STYLE, PAGE_STYLE )

def build_layout(config):
    logging.info("Building Display")
    # Load Data
    instance_metric_report_name = config['metric_dataset']
    instance_check_report_name = config['check_dataset']
    metric_df, check_df = load_historical_metric_check_reports(instance_metric_report_name, instance_check_report_name)

    latest_check_df = check_df[check_df["timestamp"]== check_df["timestamp"].max()]
    latest_metric_df = metric_df[metric_df["timestamp"]== metric_df["timestamp"].max()]
    
    ### Instance Metrics ###
    instance_metrics = []
    inst_metrics = latest_metric_df[latest_metric_df["project_id"] != latest_metric_df["project_id"]]
    for idx, row in inst_metrics.iterrows():
        if row["metric_type"] in ["INT", "FLOAT"]:
            instance_metrics.append(build_numerical_metric_card(row["metric_name"], row["metric_value"]))
        else:
            logging.info(f"metric type {row['metric_type']} not managed for instance metrics")
    
    ### Project Aggregation Metrics & Hist ###
    # Get all INT & FLOAT project avg metrics & build histograms
    mean_proj_metrics = []
    proj_metric_hists = []
    proj_metrics = latest_metric_df[latest_metric_df["project_id"] == latest_metric_df["project_id"]]
    
    for p_metric in set(proj_metrics[proj_metrics["metric_type"].isin(["INT"])]["metric_name"]):
        
        df_metric = proj_metrics[proj_metrics["metric_name"] == p_metric]
        df_metric = df_metric.astype({'metric_value': 'int64'})
        mean_proj_metrics.append(build_numerical_metric_card(f"avg {p_metric}", "{:.2f}".format(df_metric["metric_value"].mean())))
        proj_metric_hists.append(build_hist_card(p_metric, df_metric))
    
    for p_metric in set(proj_metrics[proj_metrics["metric_type"].isin(["FLOAT"])]["metric_name"]):
        
        df_metric = proj_metrics[proj_metrics["metric_name"] == p_metric]
        df_metric = df_metric.astype({'metric_value': 'float64'})
        mean_proj_metrics.append(build_numerical_metric_card(f"avg {p_metric}", "{:.2f}".format(df_metric["metric_value"].mean())))
        proj_metric_hists.append(build_hist_card(p_metric, df_metric))

    ### Project & Instance Check Category Pie Charts ###
    project_check_pie_charts = []
    instance_check_pie_charts = []
    for category in set(latest_check_df["check_category"]):
        cat_df = latest_check_df[latest_check_df["check_category"] == category]
        project_key = cat_df["project_id"].iloc[0]
        if project_key != project_key:
            instance_check_pie_charts.append(build_pie_chart_card(category, cat_df))
        else:
            project_check_pie_charts.append(build_pie_chart_card(category, cat_df))
    
    # Individual Instance Recommendations.
    instance_indiv_checks = []
    instance_check_dist = set(latest_check_df["check_name"][latest_check_df["project_id"]!=latest_check_df["project_id"]])
    
    for check_name in instance_check_dist:
        instance_indiv_checks.append(build_instance_check_card(check_name, latest_check_df))
    
    #Individual Project Recommendations.
    project_indiv_checks = []
    project_check_dist = set(latest_check_df["check_name"][latest_check_df["project_id"]==latest_check_df["project_id"]])
    
    for check_name in project_check_dist:
        proj_check_card = build_project_check_card(check_name, latest_check_df)
        if proj_check_card[1] == proj_check_card[1]: # Remove NaN checks
            project_indiv_checks.append(proj_check_card)
    project_indiv_checks_sorted = sorted(project_indiv_checks, key=lambda tup: tup[1], reverse = True)
    project_indiv_checks_sorted = [x[0] for x in project_indiv_checks_sorted]

    display = []
    display.extend([
                    dbc.Row(html.H1("PAT Report"),style = {"text-align": "center"})
                    ])
    
    if len(instance_metrics) > 0:
        display.extend([
                        dbc.Row(html.H2("Instance Metrics"),style = ROW_STYLE),
                        dbc.Row(html.Div(instance_metrics),style = ROW_STYLE)
                       ])
    
    if len(mean_proj_metrics) > 0:
        display.extend([
                        dbc.Row(html.H2("Project Agg Metrics"),style = ROW_STYLE),
                        dbc.Row(html.Div(mean_proj_metrics),style = ROW_STYLE),
                        dbc.Row(html.H2("Project Metric Distributions"),style = ROW_STYLE),
                        dbc.Row(html.Div(proj_metric_hists),style = ROW_STYLE)
                       ])
    
    if len(project_check_pie_charts) > 0:
        display.extend([
                        dbc.Row(html.H2("Project Checks Summary"),style = ROW_STYLE),
                        dbc.Row(html.Div(project_check_pie_charts),style = ROW_STYLE)
                       ])
    
    if len(instance_check_pie_charts) > 0:
        display.extend([
                        dbc.Row(html.H2("Instance Checks Summary"),style = ROW_STYLE),
                        dbc.Row(html.Div(instance_check_pie_charts),style = ROW_STYLE)
                        ])
    if len(instance_indiv_checks) > 0:
        display.extend([
                        dbc.Row(html.H2("Instance Check Recommendations"),style = ROW_STYLE),
                        dbc.Row(html.Div(instance_indiv_checks),style = ROW_STYLE)
                       ])
    if len(project_indiv_checks_sorted) > 0:
        display.extend([    
                        dbc.Row(html.H2("Project Check Recommendations"),style = ROW_STYLE),
                        dbc.Row(html.Div(project_indiv_checks_sorted),style = ROW_STYLE)
                       ])

    
    return html.Div(display, style = PAGE_STYLE)