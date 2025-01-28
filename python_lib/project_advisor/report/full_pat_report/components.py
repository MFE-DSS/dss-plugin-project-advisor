# Components
import logging
from dash import dcc, html
import dash_table
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
import random

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import (styles, font_family, base_colors)

# Helper explanation content
helper_content = dcc.Markdown('''
###### How to read the score waterfall
This bar chart shows the evolution of the Project Score over time.
The **Initial Run** bar shows the score for the first assessment, before any changes were made.
Each subsequent bar corresponds to a run where a change happened in the score. 
**Green bars** indicate improvements (positive changes), while **red bars** represent decreases in the score.

###### Project score details
The Project Score is a percentage value that measures the quality of the project based on relevant checks. It is calculated as follows:
$$
\\text{Project Score} = \\frac{\\text{Passed Checks}}{\\text{Total Relevant Checks}} \\times 100
$$
**Passed Checks**: The number of conditions or checks the project successfully meets.  
**Total Relevant Checks**: The overall number of conditions or checks that are applicable to the project.
''', mathjax=True)


#####################################################
#################### CHARTS #########################
#####################################################


def project_score_evolution(df):
    """
    Build Waterfall showing total score evolution over time
    """
    logging.info(f"Build Waterfall showing score evolution over time")
    # Consider only rows which are not null for the delta value
    df_chart = df[df.delta != 0].copy()

    # Create a new column with change labels (considering edge case where there is no change)
    if len(df_chart) == 1:
        changes = []
    elif len(df_chart) == 2:
        changes = ["Last Change"]
    else: 
         changes = [f"Change #{i}" for i in range(1, len(df_chart) - 1)] + ["Last Change"]
    
    df_chart['run_label'] = ["Initial Run"] + changes

    # Extract columns into lists
    timestamps = df_chart['timestamp'].tolist()
    project_scores = df_chart['project_score'].tolist()
    deltas = df_chart['delta'].tolist()
    run_label = df_chart['run_label'].to_list()
    
    # Settings for tooltip
    initial_run_tooltip = "Timestamp: %{customdata[0]}<br>Project Score: %{customdata[1]}"
    not_initial_run_tooltip = "Timestamp: %{customdata[0]}<br>Project Score: %{customdata[1]}<br>Delta: %{customdata[2]}<extra></extra>"
    hover_item = [initial_run_tooltip if np.isnan(delta) else not_initial_run_tooltip for delta in deltas]

    # Create a figure with a waterfall chart
    fig = go.Figure(go.Waterfall(
        name="", orientation="v",
        measure=['absolute'] + ['relative'] * (len(deltas) - 1),  # First delta is absolute, rest are relative
        x=run_label,  
        textposition="auto",  # Position of the delta values
        textfont=dict(size=14),
        text=['' if i == 0 else f'{delta:+}' for i, delta in enumerate(deltas)],  # Empty delta in the tooltip for first bar
        y=[project_scores[0]] + deltas[1:],  # Start with the base score, then deltas
        customdata=list(zip(timestamps, project_scores, deltas)),  # Include timestamps and scores in customdata
        hovertemplate=hover_item,  # Customize tooltip
        connector={"line": {"color": "rgb(63, 63, 63)"}},  
        decreasing={"marker": {"color": "#f35b05"}},  # Red for negative deltas
        increasing={"marker": {"color": "#00b257"}},  # Green for positive deltas
        totals={"marker": {"color": "#dfd1eb"}}  # Customize the final value color (if totals are calculated)
    ))

    # Update layout for better readability
    fig.update_layout(
        title=None,
        height=300,
        xaxis=dict(showgrid=True, gridcolor='LightGray'),
        yaxis=dict(title='Score (%)', showgrid=True, gridcolor='LightGray', range=[0, 100]),
        xaxis_type='category',
        showlegend=False, 
        plot_bgcolor='white', 
        hovermode='x unified',  # Unified hover mode
        margin=dict(l=0, r=10, t=10, b=10),
        font=dict(family=font_family, size=14),
    )
    
    return fig


def project_score_by_category(df):
    """
    Build a horizontal stacked bar chart for project score by category
    """
    logging.info(f"Create a horizontal stacked bar chart")
    
    
    fig = px.bar(
        df, 
        x='project_score', 
        y='category', 
        orientation='h', 
        title=None,
        text='project_score',  # Display project scores inside the bars
        color_discrete_sequence=['#4578fc']
    )

    fig.update_layout(
        xaxis=dict(
            title='Score (%)', 
            showgrid=True, 
            gridcolor='LightGray', 
            range=[0, 100], 
            showticklabels=False,  
            showticksuffix='none' 
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='LightGray',
            tickvals=df['category'], 
            ticktext=[f'{cat} ' for cat in df['category']],  # Add space to the right of the category ticks
            title=''  
        ),
        plot_bgcolor='white',
        showlegend=False,
        font=dict(family=font_family, size=14),
        height=300,
        margin=dict(l=0, r=10, t=10, b=10),
        hovermode=False
    )

    fig.update_traces(
        texttemplate='%{text} ',
        textposition='auto',
        marker_color=df['color']
    )

    return fig


def project_score_evolution_by_category(df):
    """
    Build project score by category
    """
    logging.info(f"Build project score by category")
    
    fig = go.Figure()

    categories = df['category'].unique()

    colors = ['#4578fc', '#f35b05', '#00b257', '#becaf9', "#dfd1eb", "#b8e7ba", "#fccd20"]

    # Loop over each unique category to create a separate line for each
    for i, category in enumerate(categories):
        category_data = df[df['category'] == category]
        
        # Add a line trace for the current category
        fig.add_trace(go.Scatter(
            x=category_data['date'],  
            y=category_data['project_score'],  
            mode='lines+markers',  
            name=category, 
            line=dict(color=colors[i % len(colors)], width=3), 
            marker=dict(size=7)  
        ))

    # Update the layout of the chart with titles, gridlines, and overall design
    fig.update_layout(
        title=None,
        xaxis=dict(title=None, showgrid=True, gridcolor='LightGray', tickformat='%b %d, %Y\n%H:%M:%S'),
        yaxis=dict(title='Score (%)', showgrid=True, gridcolor='LightGray'),
        plot_bgcolor='white',
        legend=dict(
                font=dict(
                    size=12  
                )
            ),
        hovermode='x unified',
        showlegend=True, 
        height=300, 
        font=dict(family=font_family, size=14), 
        margin=dict(l=10, r=10, t=10, b=10)
    )

    # Add hover template
    fig.update_traces(
        hovertemplate='Date: %{x}<br>Score: %{y}', 
        selector=dict(type='scatter')  
    )

    return fig


def create_fail_to_pass_table(changed_to_pass):
    """
    Create fail to pass table
    """
    logging.info(f"Create fail to pass table")
    
    table_fail_to_pass = dash_table.DataTable(
        columns=[{"name": i.replace("_", " ").title(), "id": i} for i in changed_to_pass.columns],
        data=changed_to_pass.to_dict('records'),
        style_cell={'textAlign': 'left', 'padding': '5px', 'font-family': font_family},
        style_as_list_view=True,
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{status_change} = "Fail to Pass"',
                    'column_id': 'status_change'
                },
                'backgroundColor': 'green',
                'color': 'white',
            }
        ],
    )
    
    return table_fail_to_pass


def create_check_reco_accordion(check_reco_df): 
    """
    Create check reco accordion
    """
    logging.info(f"Create check reco accordion")
    
    categories = check_reco_df.groupby('check_category')
    accordion_items = []

    for category_name, category_df in categories:
        # Check if any check in this category failed
        has_failed_check = category_df['pass'].eq(False).any()

        # Add warning icon if any check failed in the category
        category_header = html.Span([
            html.Span(category_name),
            html.I(className="bi bi-exclamation-triangle-fill text-warning ms-2") if has_failed_check else None
        ])

        # Create a list of individual checks within the category
        checks = []

        for _, row in category_df.iterrows():
            check_passed = row['pass']
            check_name = row['check_name']
            check_message = row['message']
            check_result = json.loads(row['result_data'])
            
            # Add warning icon if any check failed in the category
            check_header = html.Span([
                html.Span(["Check: ", check_name.replace("_check", "").replace("_", " ").capitalize()]),
                html.I(className="bi bi-check-circle-fill text-success ms-2") if check_passed else html.I(className="bi bi-x-octagon-fill text-danger ms-2")
            ])

            check_style = {
                'color': 'black',
                'padding': '10px',
                'border': '1px solid #ddd'
            }
           
            # If the check failed, display it with the recommendation
            check_content = html.Div([
                html.P(f"Description: {check_result['description']}") if check_result['description'] else None,
                html.P(f"Message: {check_message}" if check_message else None),
                html.P(f"Additional details: {check_result['run_result']}") if not check_passed else None
            ], style=check_style)

            checks.append(dbc.AccordionItem(
                check_content,
                title=check_header,
                item_id=f"check-{row['check_name']}",
                style=check_style,
            ))

        # Add category as an accordion item
        accordion_items.append(dbc.AccordionItem(
            checks,
            title=category_header,
            item_id=f"category-{category_name}"
        ))
    return dbc.Accordion(
        accordion_items,
        always_open=True,  # Keep accordion categories open to see checks easily
        flush=True,
        start_collapsed=True
    )


def generate_metric_cards(df_metrics):
    """
    Building generic metric cards
    """
    logging.info(f"Building generic metric cards")
    
    cards_per_row = 6
    rows = []

    # Split the dataframe into chunks of 5 rows
    for i in range(0, len(df_metrics), cards_per_row):
        row_cards = []

        for _, metric in df_metrics.iloc[i:i + cards_per_row].iterrows():
            metric_value = str(int(float(metric['metric_value']))) if metric['metric_type'] == 'INT' else metric['metric_value']
            metric_metadata = json.loads(metric['result_data'])
            metric_unit = metric_metadata.get("metric_unit")
            
            # Case where metric has a unit
            if metric_unit:
                metric_value = f"{metric_value} {metric_unit}"
            
            card = dbc.Card([
                dbc.CardHeader(f"{metric['metric_name'].replace('_', ' ').replace('nbr', '#').replace('percentage', '%').capitalize()}", 
                               style={"height": "70px", 'display': 'flex', "align-items": "center", 'justify-content': 'center', 'overflow': 'hidden', "font-size": "14px", 'white-space': 'wrap', 'text-overflow': 'ellipsis'}),
                dbc.CardBody(
                    [
                        html.H3(f"{metric_value}", className="card-title") ,
                        html.P(f"{metric_metadata['description'].replace('.','')}", className="card-text", style={"font-size": "12px"}),
                    ]
                )],
                style={"height": "100%", "text-align": "center"},
            )
            row_cards.append(dbc.Col(card, width=12 // cards_per_row))  # 2 units width to fit 6 cards in a row

        # Add the row to the list of rows
        rows.append(dbc.Row(row_cards, justify="start", style={"margin-bottom": "20px"}))

    return rows


def metric_evolution(df):
    """
    Building metric evolution
    """
    logging.info(f"Building metric evolution")
    
    fig = go.Figure()

    metric_name = df['metric_name'].unique()

    # Define color palette for the categories (you can expand the palette as needed)
    colors = generate_colors(len(metric_name))

    # Loop over each unique category to create a separate line for each
    for i, metric in enumerate(metric_name):
        metric_data = df[df['metric_name'] == metric]
        
        # Add a line trace for the current category
        fig.add_trace(go.Scatter(
            x=metric_data['timestamp'],  
            y=metric_data['metric_value'], 
            mode='lines+markers',  
            name=metric.replace("nbr", "#").replace("_", " ").replace("percentage", "%").capitalize(), 
            line=dict(color=colors[i % len(colors)], width=3), 
            marker=dict(size=7) 
        ))

    # Update the layout of the chart with titles, gridlines, and overall design
    fig.update_layout(
        title=None,
        xaxis=dict(title=None, showgrid=True, gridcolor='LightGray', tickformat='%b %d, %Y\n%H:%M:%S'),
        yaxis=dict(title='Metric value', showgrid=True, gridcolor='LightGray'),
        plot_bgcolor='white',  
        legend=dict(
                font=dict(
                    size=12 
                )
            ),
        hovermode='x unified',  
        showlegend=True,  
        height=300,
        font=dict(family=font_family, size=14),
        margin=dict(l=10, r=10, t=10, b=10)
    )

    # Add hover template for better readability
    fig.update_traces(
        hovertemplate='Date: %{x}<br>Metric value: %{y}', 
        selector=dict(type='scatter')  
    )

    return fig
            
    
def generate_colors(num_categories):
    """
    If number of categories is less than or equal to the number of base colors, just return the base colors
    """
    if num_categories <= len(base_colors):
        return base_colors[:num_categories]
    
    # If number of categories exceeds base colors, generate more colors by randomizing shades
    generated_colors = base_colors.copy()
    while len(generated_colors) < num_categories:
        # Randomly lighten or darken an existing color slightly to create more variety
        new_color = random.choice(base_colors)
        # Modify the color a little bit to create a variation (change brightness or saturation)
        # Adjust the RGB values slightly
        new_color_variation = lighten_or_darken_color(new_color, random.uniform(-0.2, 0.2))
        generated_colors.append(new_color_variation)
    
    return generated_colors[:num_categories]


# Helper function to lighten or darken a color
def lighten_or_darken_color(color, factor):
    # Convert hex color to RGB
    color = color.lstrip('#')
    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    
    # Adjust the color by factor (-1 to 1 where negative darkens, positive lightens)
    r = int(max(min(r * (1 + factor), 255), 0))
    g = int(max(min(g * (1 + factor), 255), 0))
    b = int(max(min(b * (1 + factor), 255), 0))
    
    # Convert back to hex
    return f'#{r:02x}{g:02x}{b:02x}'






