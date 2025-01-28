import dash
import logging
from dash.dependencies import Input, Output, State, ALL



def collapse_callback(app):
    @app.callback(
        [Output({'type': 'collapse-check-content', 'index': ALL}, "is_open")],
        [Input({'type': 'collapse-check-button', 'index': ALL}, "n_clicks")],
        [State({'type': 'collapse-check-content', 'index': ALL}, "is_open")],
    )
    def collapse(buttons, check_content):
        logging.info(f"Callback collapse")
        args_grouping = dash.callback_context.args_grouping
        logging.debug(f"args_grouping : {args_grouping}")
        
        collapse_buttons = args_grouping[0]
        collapse_content = args_grouping[1]

        triggered_idx = None
        for cb in collapse_buttons:
            if cb["triggered"]:
                triggered_idx = cb['id']['index']
        
        logging.info(f"Callback collapse triggered by : {triggered_idx}")
        collapse_update = []
        for cc in collapse_content:
            is_open = cc["value"]
            if cc["id"]["index"] == triggered_idx:
                is_open = not is_open
            collapse_update.append(is_open)

        return [collapse_update]