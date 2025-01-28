# Main display
import logging
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles

def build_layout(input_config, data):
    """
    Generate Main Layout for the whole webapp
    """
    logging.info("Generate Main Layout for the whole webapp")
    
    #batch_pat_tab = {'label': html.Span(['Batch Project Assessment Tool', html.I(className="fas fa-lock", style={'margin-left': '10px'})]), 'value': 'batch', 'disabled': True}
    
    # If user is admin
    #instance_pat_tab = {'label': 'Instance Assessment Tool', 'value': 'instance'}
    
    # If user is not admin
    #instance_pat_tab = {'label': html.Span(['Instance Assessment Tool', html.I(className="fas fa-lock", style={'margin-left': '10px'})]), 'value': 'instance', 'disabled': True}
    
    
    # Sidebar
    sidebar = dbc.Col([
                html.H2(html.Span([html.I(className="fa-solid fa-chart-line", style={'margin-right': '10px'}), "PAT Report (PAT v1.4)"]), className="display-6", style=styles["sidebar_header"]),
                html.Div([
                    html.P("Please select the type of assessment:", style={"color": "white", "font-size": 14}), 

                    # Dropdown for Tab options
                    html.Div(id = "layout-dropdown-div"),

                    # Placeholder for the dynamic dropdown
                    html.Div(id='dynamic-dropdown-container'),

                    # Placeholder for project details
                    html.Div(id='project-details-content')

                ], className="bg-dark", style=styles["sidebar_content"]),

                # Footer section
                html.Div([
                    html.Div([
                        html.P("Any questions or bugs to report?", style={"marginBottom": "0.5rem"}),
                        html.P("Please contact the Dataiku team", style={"marginBottom": "0"})
                    ], style=styles["footer_content"])
                ], style=styles["sidebar_footer"]),

            ], width=3, style=styles["sidebar_container"])


    # Main content
    main_content = dbc.Col([

                        # Top white bar
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Div([
                                        html.P(children=["Hello"], id="menu-user", style={"padding": "10px 20px", "font-size": 20, "color": "#495057", "margin-top": "5px"})
                                    ], className="d-flex justify-content-end"),
                                ], style=styles["top_white_bar"])
                            ])
                        ]),

                        # Content
                        html.Div(id="layout")
        ], 
        width=9, 
        style=styles["content_container"]
    )
    
    memory = html.Div([
                    dcc.Store(id='example-id')]
    )

    # Define the layout
    main_layout =  dbc.Container([
        dbc.Row([
            sidebar,
            main_content
        ]),
        html.Div(id="my-input"), # For input of 
        memory,
    ], fluid=True, style=styles["page_style"])
    
    return main_layout