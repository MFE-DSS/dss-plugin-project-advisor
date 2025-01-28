# Callbacks
import dash
import logging
from dash.dependencies import Input, Output, State, ALL
from dash import dcc, html
from flask import request
from dash import callback_context


from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles
from project_advisor.report.full_pat_report.tools import (enrich_project_list,
                                                          user_is_admin,
                                                          get_user_project_keys,
                                                          
                                                         )
                                                          

from project_advisor.report.full_pat_report.tabs import (generate_homepage_single_pat,
                                                         generate_layout_single_pat, 
                                                         generate_layout_instance_pat,
                                                         generate_project_details
                                                         )


def get_authenticated_user_id():
    """
    get user auth info
    Note : Only callable within a callback
    """
    logging.info("get user authentication info")
    
    client = configs["client"]
    request_headers = dict(request.headers)
    auth_info = client.get_auth_info_from_browser_headers(request_headers)
    return auth_info["authIdentifier"]



def load_callbacks(app, data):
    """
    Init Callbacks
    """
    logging.info(f"Init Callbacks")
    
    # Init variables for callbacks
    client = configs["client"]
    check_df = data["check_df"]
    metric_df = data["metric_df"]
    user_to_project_df = data["user_to_project_df"]
    is_instance_report = data["is_instance_report"]
    
    # All CHECKED projects on the INSTANCE
    list_project_ids = list(check_df["project_id"].unique())
    all_project_list = enrich_project_list(list_project_ids)
    
    # Callback to identify user
    @app.callback(
        Output('menu-user', 'children'),
        Output('layout-dropdown-div', 'children'),
        [Input('my-input', 'children')]
    )
    def update_user(input_value):
        """
        Load user using webapp
        """
        logging.info(f"Load user using webapp")
        
        user_id = get_authenticated_user_id()
        users = client.list_users()
        user_name = next((user['displayName'] for user in users if user['login'] == user_id), "Unknown")
        logging.info(f"User with username : {user_name} has been identified")
        
        ### Define drop down options
        # Project Tab option (always on)
        project_pat_tab = {'label': 'Project Assessment Tool', 'value': 'project'}
        
        # Batch Project Tab option (always on)
        batch_pat_tab = {'label': html.Span(['Batch Project Assessment Tool', html.I(className="fas fa-lock", style={'margin-left': '10px'})]), 'value': 'batch', 'disabled': True}

        # Instance Tab option
        # If instance user is admin, give access to Instance PAT.
        if user_is_admin(user_id) and is_instance_report:
            instance_pat_tab = {'label': 'Instance Assessment Tool', 'value': 'instance'}
        else:
            instance_pat_tab = {'label': html.Span(['Instance Assessment Tool', html.I(className="fas fa-lock", style={'margin-left': '10px'})]), 'value': 'instance', 'disabled': True}
        
        # Define drop down options
        options = [project_pat_tab, batch_pat_tab, instance_pat_tab]
        
        main_drop_down = dcc.Dropdown(
                                    id='layout-dropdown',
                                    options=options,
                                    value='project',  # Default value
                                    className='mb-3',
                                    style=styles["dropdown_style"],
                                )
        
        
        return f"Hello {user_name}", main_drop_down
    
    
    # Callback to update the dynamic dropdown (project-dropdown) based on the selected tool
    @app.callback(
        Output('dynamic-dropdown-container', 'children'),
        Input('layout-dropdown', 'value')
    )
    def update_dynamic_dropdown(selected_tool):
        """
        Update dynamic drop downs
        """
        logging.info(f"Update dynamic drop downs")
        
        user_login = get_authenticated_user_id()
        
        user_project_list = []
        if user_is_admin(user_login):
            user_project_list = all_project_list
        else:
            user_project_keys = get_user_project_keys(user_login, user_to_project_df)
            user_project_list = [p for p in all_project_list if list(p.keys())[0] in user_project_keys]
        
        
        if selected_tool == 'project':
            # Return the project selection dropdown for 'project' tool
            
            options_project = [{'label': list(project.keys())[0], 'value': list(project.keys())[0]} for project in user_project_list]
    
            return [
                html.P("Please select a project:", style={"color": "white", "font-size": 14}),
                dcc.Dropdown(
                    id='project-dropdown',
                    options=options_project,  
                    placeholder="Select a project",
                    className='mb-3',
                    style=styles["dropdown_style"]
                )
            ]
        else:
            # Return nothing for other tools
            return None


    # Define callback to update content based on dropdown selection
    @app.callback(
        [Output('layout', 'children'),
         Output('project-details-content', 'children')],
        [Input('layout-dropdown', 'value'),
         Input('dynamic-dropdown-container', 'children'),
         Input('project-dropdown', 'value')]
    )
    def update_main_content(selected_tool, dynamic_dropdown, selected_project):
        """
        Update main content
        """
        logging.info(f"Update main content")
        
        ctx = callback_context
        
        # Define user project list.
        user_project_list = all_project_list
        
        
        # Determine which input triggered the callback
        if not ctx.triggered or selected_tool == 'project':
            if selected_project is None:
                # If no project is selected, show the message
                return generate_homepage_single_pat(), dash.no_update
            else:
                # If a project is selected, show the project layout
                return generate_layout_single_pat(selected_project, 
                                                  user_project_list, 
                                                  data), \
                       generate_project_details(selected_project, user_project_list, styles)

        elif selected_tool == 'instance':
            return generate_layout_instance_pat(all_project_list, data), None

        elif selected_tool == 'batch':
            return dbc.Row([
                dbc.Col(html.Div("Batch Project Assessment Tool Content", className="mb-3"), width=12)
            ]), dash.no_update

        return None, dash.no_update
    

    