# Tabs (in the main display)
import logging
from dash import dcc, html
import dash_bootstrap_components as dbc

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles

from project_advisor.report.full_pat_report.components import (project_score_evolution,
                                                               project_score_by_category,
                                                               project_score_evolution_by_category,
                                                               create_fail_to_pass_table,
                                                               create_check_reco_accordion,
                                                               generate_metric_cards,
                                                               metric_evolution,
                                                               helper_content
                                                              )

from project_advisor.report.full_pat_report.tools import (compute_fail_to_pass_df,
                                                          compute_check_reco_table_df,
                                                          compute_metric_df
                                                         )

def generate_homepage_single_pat():
    """
    Generate Homepage single PAT
    """
    logging.info("Generate Homepage single PAT")
    
    layout_homepage_single_pat = html.Div([
        html.Div([
            html.Span([
                html.I(className="bi bi-sliders", style={"font-size": "2rem"})
            ]),
            html.H2([
            "Select a project or choose a different tool from the sidebar on the left"
            ], style={"font-size": "22px", "font-color": "#495057", "margin-top": "20px"})
        ], style=styles["homepage_single_pat"])
    ], style=styles["div_homepage_single_pat"])
    return layout_homepage_single_pat


def generate_project_details(project_key, project_list, styles):
    """
    Generate Project Details
    """
    logging.info("Generate Project Details")
    
    # Fetch the relevant project data based on the project_key
    project = next(proj for proj in project_list if project_key in proj)
    project_name = project[project_key]["name"]
    project_type = project[project_key]["project_type"]
    project_owner = project[project_key]["owner"]

    project_details = html.Div([
        html.H6(
            html.Span([
                html.I(className="fa-solid fa-circle-info", style={'margin-right': '10px'}),
                "Project details"
            ]),
            className="text-white",
            style={"font-size": "16px"}
        ),
        html.Hr(style={"color": "white"}),
        html.P(f"Project name: {project_name}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
        html.P(f"Project key: {project_key}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
        html.P(f"Project type: {project_type}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
        html.P(f"Project owner: {project_owner}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
    ], id='project-details', style=styles["sidebar_project_details"])

    return project_details

def generate_layout_single_pat(project_key, project_list, data):
    """
    Generate the layout for the single PAT Tab
    """
    logging.info("Generate the layout for the single PAT Tab")
    
    project_categories = configs["project_categories"]
    check_df = data["check_df"]
    metric_df = data["metric_df"]
    precomputed_result_project_df = data["precomputed_result_project_df"] 
    precomputed_project_by_category_df = data["precomputed_project_by_category_df"]
    
    # Compute project scores for all timestamps
    project_scores_df = precomputed_result_project_df[precomputed_result_project_df["project_id"] == project_key]
    most_recent_timestamp = project_scores_df['timestamp'].max()
    project_score_value = int(project_scores_df[project_scores_df['timestamp'] == most_recent_timestamp]['project_score'].iloc[0])
    most_recent_timestamp_str = most_recent_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    project_score_str = f"Project score: {project_score_value}%"

    # Generate project score evolution chart
    fig_project_score_evol = project_score_evolution(project_scores_df)
    
    # Compute project scores by category
    project_by_category_df = precomputed_project_by_category_df[precomputed_project_by_category_df["project_id"] == project_key]
    most_recent_date = project_by_category_df['date'].max()
    most_recent_project_scores_category_df = project_by_category_df[project_by_category_df['date'] == most_recent_date]

    # Charts for project scores by category and evolution
    fig_project_score_category = project_score_by_category(most_recent_project_scores_category_df)
    fig_scores_by_category_evol = project_score_evolution_by_category(project_by_category_df)

    # Failed to pass dataframe and table
    project_df = check_df[check_df["project_id"] == project_key]
    fail_to_pass_df = compute_fail_to_pass_df(project_df, category=project_categories)
    table_fail_to_pass = create_fail_to_pass_table(fail_to_pass_df) if not fail_to_pass_df.empty else html.P("No changes in check status during the last run.", className="text-muted")

    # Check recommendations table
    check_reco_df = compute_check_reco_table_df(project_df, category=project_categories)
    table_check_reco = create_check_reco_accordion(check_reco_df)

    # Metric cards and evolution chart
    df_metric_project = metric_df[metric_df['project_id'] == project_key].copy()
    project_metric_df = compute_metric_df(df_metric_project, instance=False)
    most_recent_timestamp = project_metric_df['timestamp'].max()
    project_metric_last_df = project_metric_df[project_metric_df['timestamp'] == most_recent_timestamp]
    cards_metric_project = generate_metric_cards(project_metric_last_df)
    fig_metric_evolution = metric_evolution(project_metric_df)

    # Layout structure
    layout = dbc.Row([
        dbc.Col([
            
            # Row containing project score and report date
            dbc.Row(
                [
                    # Col for the Project Score
                    dbc.Col(
                        html.Div(
                            [
                                html.H3([dbc.Badge(project_score_str, id="project_score", color="#fccd20", text_color="dark", className="me-1")], style={"display": "inline-block"}),
                                html.I(className="bi bi-info-circle-fill me-2", id="target_info", style={'display': 'inline-block', 'margin-left':'5px', 'font-size': 20}),
                                dbc.Tooltip(
                                    "The project score is the ratio between the passed checks and the overall relevant checks.",
                                    target="target_info",
                                    style={"font-size": 13}
                                )
                            ],
                            style={"font-size": "24px", "font-weight": "bold"},
                        ),
                        width=6,  # Adjust the width for alignment
                    ),
                    
                    # Col for the Report Date
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("Last report date: ", style={"font-weight": "bold"}),
                                html.Span(most_recent_timestamp_str, id="report_date"),
                            ],
                            style={"font-size": "20px", "text-align": "right"},
                        ),
                        width=6,  # Adjust width as needed
                    ),
                ],
                className="align-items-center",  # Ensures vertical alignment
                style= {"margin-bottom": "20px"}
            ),
            
            # Project score evolution
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Project score evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_project_score_evol), 
                        ]),
                    ], className="mb-4"),
                ], md=8),
                
                # Add the helper div next to the graph
                dbc.Col([
                    html.Div([
                        helper_content
                    ], style={
                        "background-color": "#d9e6ed", 
                        "color": "#205678", 
                        "border-radius": "8px", 
                        "padding": "15px", 
                        "font-size": "12px",
                        "height": "397.29px",
                        'overflow': 'hidden',  
                        'maxWidth': '100%', 
                        'wordWrap': 'break-word',
                    }),
                ], md=4),
            ]),
            
            # Checks summary
            html.H3("Checks summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Project scores by category (last run)", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_project_score_category), 
                        ]),
                    ], className="mb-4"),
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Evolution of project scores by category", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_scores_by_category_evol)
                        ]),
                    ], className="mb-4"),
                ], md=8),
            ]),
            
            # Checks details
            html.H3("Check details", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Flag changing check status (last run)", style={"font-size": 20}),
                        dbc.CardBody([
                            table_fail_to_pass
                        ]),
                    ], className="mb-4"),
                ], md=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Check recommendations", style={"font-size": 20}),
                        dbc.CardBody([
                            table_check_reco
                        ]),
                    ], className="mb-4"),
                ], md=12),
            ]),
            
            # Metrics summary
            html.H3("Metrics summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            html.P("Metrics below are computed during the last run", style={"padding": "10px", "font-style": "italic"}),
            
            html.Div(cards_metric_project, style={"width": "100%"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Metrics evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_metric_evolution), 
                        ]),
                    ], className="mb-4"),
                ], md=8),
            ]),
        ], style=styles["content_page"])
    ], style=styles["content_page_row"])

    return layout




def generate_layout_instance_pat(project_list, data):
    """
    Generate Layout for the instance PAT TAB
    """
    logging.info("Generate Layout for the instance PAT TAB")
    
    instance_categories = configs["instance_categories"]
    check_df = data["check_df"]
    metric_df = data["metric_df"]
    precomputed_result_project_df = data["precomputed_result_project_df"]
    precomputed_result_instance_df = data["precomputed_result_instance_df"]
    precomputed_instance_by_category_df = data["precomputed_instance_by_category_df"]
    
    
    
    # Compute project scores for all timestamps
    most_recent_timestamp = precomputed_result_project_df['timestamp'].max()
    project_score_value = int(precomputed_result_project_df[precomputed_result_project_df['timestamp'] == most_recent_timestamp]['project_score'].iloc[0])
    most_recent_timestamp_str = most_recent_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    project_score_str = f"Average project score: {project_score_value}%"
    
    # Compute instance score for all timestamps
    most_recent_timestamp = precomputed_result_instance_df['timestamp'].max()
    instance_score_value = int(precomputed_result_instance_df[precomputed_result_instance_df['timestamp'] == most_recent_timestamp]['project_score'].iloc[0])
    most_recent_timestamp_str = most_recent_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    instance_score_str = f"Instance score: {instance_score_value}%"

    # Generate project score evolution chart
    precomputed_result_project_df = precomputed_result_project_df.sort_values(by=['project_id', 'timestamp'])
    project_score_evol_df = precomputed_result_project_df.groupby('timestamp').agg({
        'project_score': 'mean'  # Average project score per timestamp
    }).reset_index()
    project_score_evol_df['delta'] = project_score_evol_df['project_score'].diff().round(2)
    fig_project_score_evol = project_score_evolution(project_score_evol_df)
    
    # Generate instance score evolution chart
    fig_instance_score_evol = project_score_evolution(precomputed_result_instance_df)
    
    # Compute instance scores by category
    most_recent_date = precomputed_instance_by_category_df['date'].max()
    most_recent_project_scores_category_df = precomputed_instance_by_category_df[precomputed_instance_by_category_df['date'] == most_recent_date]

    # Charts for project scores by category and evolution
    fig_project_score_category = project_score_by_category(most_recent_project_scores_category_df)
    fig_scores_by_category_evol = project_score_evolution_by_category(precomputed_instance_by_category_df)

    # Failed to pass dataframe and table
    fail_to_pass_df = compute_fail_to_pass_df(check_df, category=instance_categories)
    table_fail_to_pass = create_fail_to_pass_table(fail_to_pass_df) if not fail_to_pass_df.empty else html.P("No changes in check status during the last run.", className="text-muted")

    # Check recommendations table
    check_reco_df = compute_check_reco_table_df(check_df, category=instance_categories)
    table_check_reco = create_check_reco_accordion(check_reco_df)

    # Metric cards and evolution chart
    project_metric_df = compute_metric_df(metric_df, instance=True)
    most_recent_timestamp = project_metric_df['timestamp'].max()
    project_metric_last_df = project_metric_df[project_metric_df['timestamp'] == most_recent_timestamp]
    cards_metric_project = generate_metric_cards(project_metric_last_df)
    fig_metric_evolution = metric_evolution(project_metric_df)

    # Layout structure
    layout = dbc.Row([
        dbc.Col([
            
            # Row containing project score and report date
            dbc.Row(
                [
                    # Col for the Project Score
                    dbc.Col(
                        html.Div(
                            [
                                html.H3([dbc.Badge(instance_score_str, id="instance_score", color="#4578fc", text_color="white", className="me-1")], style={"display": "inline-block"}),
                                html.H3([dbc.Badge(project_score_str, id="project_score", color="#fccd20", text_color="dark", className="me-1")], style={"display": "inline-block"}),
                                html.I(className="bi bi-info-circle-fill me-2", id="target_info", style={'display': 'inline-block', 'margin-left':'5px', 'font-size': 20}),
                                dbc.Tooltip(
                                    "The project score is the ratio of passed checks to total relevant checks, while the instance score applies the same definition to instance-level checks.",
                                    target="target_info",
                                    style={"font-size": 13}
                                )
                            ],
                            style={"font-size": "24px", "font-weight": "bold"},
                        ),
                        width=6,  # Adjust the width for alignment
                    ),
                    
                    # Col for the Report Date
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("Last report date: ", style={"font-weight": "bold", "font-size": 20}),
                                html.Span(most_recent_timestamp_str, id="report_date"),
                            ],
                            style={"font-size": "16px", "text-align": "right"},
                        ),
                        width=6,  # Adjust width as needed
                    ),
                ],
                className="align-items-center",  # Ensures vertical alignment
                style= {"margin-bottom": "20px"}
            ),
            
            # Instance and project score evolution
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Instance score evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_instance_score_evol), 
                        ]),
                    ], className="mb-4"),
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Average project score evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_project_score_evol), 
                        ]),
                    ], className="mb-4"),
                ], md=6),
            ]),
            
            # Checks summary
            html.H3("Checks summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Project scores by category (last run)", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_project_score_category), 
                        ]),
                    ], className="mb-4"),
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Evolution of project scores by category", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_scores_by_category_evol)
                        ]),
                    ], className="mb-4"),
                ], md=8),
            ]),
            
            # Checks details
            html.H3("Check details", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Flag changing check status (last run)", style={"font-size": 20}),
                        dbc.CardBody([
                            table_fail_to_pass
                        ]),
                    ], className="mb-4"),
                ], md=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Check recommendations", style={"font-size": 20}),
                        dbc.CardBody([
                            table_check_reco
                        ]),
                    ], className="mb-4"),
                ], md=12),
            ]),
            
            # Metrics summary
            html.H3("Metrics summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            html.P("Metrics below are computed during the last run", style={"padding": "10px", "font-style": "italic"}),
            
            html.Div(cards_metric_project, style={"width": "100%"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Metrics evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_metric_evolution), 
                        ]),
                    ], className="mb-4"),
                ], md=8),
            ]),
        ], style=styles["content_page"])
    ], style=styles["content_page_row"])

    return layout