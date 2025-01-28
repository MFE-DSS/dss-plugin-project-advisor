import pandas as pd
import numpy as np
import copy
import logging

import plotly.express as px
import matplotlib as mpl

import dash_bootstrap_components as dbc
from dash import dcc, html

from project_advisor.report.instance_report.style import (GREEN,
                                                          YELLOW,
                                                          RED,
                                                          GRAY,
                                                          NUM_METRIC_CARD_STYLE,
                                                          NUM_METRIC_CARD_BODY_STYLE,
                                                          HIST_METRIC_CARD_STYLE,
                                                          HIST_METRIC_CARD_BODY_STYLE,
                                                          CAT_CHART_CARD_STYLE,
                                                          CAT_CHART_CARD_BODY_STYLE,
                                                          CHECK_BUTTON_STYLE
                                                         )

### COMPONENTS ###


def format_name(name : str) -> str:
    name = name.replace("_", " ")
    name = name.replace("number", "#")
    name = name.replace("nbr", "#")
    return name

def build_numerical_metric_card(metric_name : str, metric_value :int):
    logging.info(f"building numerical metrics card for metric : {metric_name}")
    return dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(format_name(metric_name), className="card-title"),
                            html.Div(
                                html.H1(
                                    metric_value,
                                    className="card-text"
                                    )
                            )    
                        ],style = NUM_METRIC_CARD_BODY_STYLE
                            ),
                ],
                style=NUM_METRIC_CARD_STYLE,
)

def build_hist_card(metric_name : str, df: pd.DataFrame):
    logging.info(f"building histogram for project metric : {metric_name}")
    fig = px.histogram(df, 
                       x="metric_value", 
                       labels= {"metric_value" : format_name(metric_name)},
                       width= 500, 
                       height= 300,
                       )
    fig.update_layout(yaxis_title="project count") 
    fig.update_layout(bargap=0.1)


    return dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(format_name(metric_name), className="card-title"),
                            html.Div(
                                dcc.Graph(figure=fig)
                            )    
                        ],style = HIST_METRIC_CARD_BODY_STYLE
                            ),
                ],
                style=HIST_METRIC_CARD_STYLE,
)

def build_pie_chart_card(category : str, df: pd.DataFrame):
    logging.info(f"Building check pie chart for category : {category}")
    
    df = df.reset_index()
    df["pass"] = df["pass"].transform( lambda x : str(x))
    fig = px.pie(df, 
             names = "pass",
             color = 'pass',
             color_discrete_map= {"True":GREEN,
                                 "False":RED,
                                 "nan" : GRAY},
             width= 250, 
             height= 250,
            )
    fig.update_layout(showlegend=False)
    return dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(category, className="card-title"),
                            html.Div(
                                dcc.Graph(figure=fig)
                            )    
                        ],style = CAT_CHART_CARD_BODY_STYLE
                            ),
                ],
                style=CAT_CHART_CARD_STYLE,
    )

def build_instance_check_card(check_name : str,
                              latest_check_df: pd.DataFrame):
    logging.info(f"Building instance check card for check : {check_name}")
    inst_check = latest_check_df[latest_check_df["check_name"] == check_name].iloc[0]
    message = inst_check["message"]
    result_data = inst_check["result_data"]
    check_pass = inst_check["pass"]

    if check_pass:
        color = GREEN
    else:
        color = RED
    button_style = copy.deepcopy(CHECK_BUTTON_STYLE)
    button_style.update({"background-color" : color})
        
        
    return html.Div(
                    [
                        dbc.Button(
                            format_name(check_name).upper(),
                            id={'type': 'collapse-check-button', 'index': check_name},
                            className="mb-3",
                            n_clicks=0,
                            style = button_style
                        ),
                        dbc.Collapse(
                            dbc.Card(dbc.CardBody(str(check_pass) + ": "  + str(message) + "\n" + str(result_data) )),
                            id={'type': 'collapse-check-content', 'index': check_name},
                            is_open=False,
                        ),
                    ]
    )

def color_fader(score=0): #fade (linear interpolate) from color c1 (at mix=0) to c2 (mix=1)
    # 0-0.5 -> red to yellow
    # 0.5 - 1 -> yellow to green
    if score != score:
        return GRAY
    mix = 0
    color_edge = 0.5 # must be > 0
    if score < color_edge:
        c1 = RED
        c2 = YELLOW
        mix = score * (1/color_edge)
    else:
        c1 = YELLOW
        c2 = GREEN
        mix = (score - color_edge) * (1/(1-color_edge))
    c1=np.array(mpl.colors.to_rgb(c1))
    c2=np.array(mpl.colors.to_rgb(c2))
    return mpl.colors.to_hex((1-mix)*c1 + mix*c2)


def build_project_check_card(check_name : str,
                              latest_check_df: pd.DataFrame):
    logging.info(f"Building project check card for check : {check_name}")
    project_checks = latest_check_df[latest_check_df["check_name"] == check_name]
    failing_projects = list(project_checks[project_checks["pass"] == False]["project_id"])
    
    score = project_checks["pass"].mean()
    button_style = copy.deepcopy(CHECK_BUTTON_STYLE)
    button_style.update({"background-color" : color_fader(score)})

    return (html.Div(
                    [
                        dbc.Button(
                            format_name(check_name).upper() + " - " + "{:.2f}".format(score * 100) + "%",
                            id={'type': 'collapse-check-button', 'index': check_name},
                            className="mb-3",
                            n_clicks=0,
                            style = button_style
                        ),
                        dbc.Collapse(
                            dbc.Card(dbc.CardBody(format_name(check_name).upper() + " - PROJECTS TO REVIEW : " + str(failing_projects))),
                            id={'type': 'collapse-check-content', 'index': check_name},
                            is_open=False,
                        ), 
                   ]
    ), score)