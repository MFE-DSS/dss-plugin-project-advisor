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

from project_advisor.report.instance_report.callbacks import collapse_callback
from project_advisor.report.instance_report.display import build_layout

logging.info('Webapp Initializing')

config = get_webapp_config()

#########################
######   DISPLAY   ######
#########################

#app.config.external_stylesheets =[dbc.themes.ZEPHYR, dbc.icons.BOOTSTRAP]

app.config.external_stylesheets = ["https://fonts.googleapis.com/css2?family=Outfit:wght@100;200;300;400;500;600;700;800;900&display=swap", dbc.themes.ZEPHYR, dbc.icons.BOOTSTRAP, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"]

app.title = "PAT Report"
app.layout = build_layout(config)

#########################
######  CALLBACKS  ######
#########################

collapse_callback(app)

logging.info('Webapp Initialized')