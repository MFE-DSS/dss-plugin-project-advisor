from dataiku.customwebapp import *
import dataiku
import logging

import pandas as pd
import numpy as np
#from datetime import datetime
import plotly.express as px
import matplotlib as mpl

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL

from project_advisor.report.full_pat_report.callbacks import load_callbacks
from project_advisor.report.full_pat_report.display import build_layout

from project_advisor.report.full_pat_report.data_loader import load_pat_report_data

logging.info('Webapp Initializing')

input_config = get_webapp_config()

#########################
######   DISPLAY   ######
#########################

# Initialize Dash app
app.config.external_stylesheets=[
    #"https://fonts.googleapis.com/css2?family=Outfit:wght@100;200;300;400;500;600;700;800;900&display=swap",
    dbc.themes.ZEPHYR, dbc.icons.BOOTSTRAP, 
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"
]

# Define font family
font_family = "Source Sans Pro"


app.title = "PAT Report"
data = load_pat_report_data(input_config)
app.layout = build_layout(input_config, data)

#########################
######  CALLBACKS  ######
#########################

load_callbacks(app, data)

logging.info('Webapp Initialized')