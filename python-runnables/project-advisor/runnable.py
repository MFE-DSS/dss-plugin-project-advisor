# This file is the actual code for the Python runnable project-advisor
import dataiku
from datetime import datetime
import logging
import re
import pandas as pd

from dataiku.runnables import Runnable

from dataiku.customstep import get_plugin_config
from dataiku.customstep import get_step_config
from dataiku.customstep import get_step_resource

from project_advisor.advisors.project_advisor import ProjectAdvisor

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder

from project_advisor.report.project_report import ProjectReportDashboardGenerator

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
        ### INITIALISATION 
        client = dataiku.api_client()
        project = client.get_default_project()
        
        assessment_config = DSSAssessmentConfigBuilder.build_from_macro_config(config = config, plugin_config = plugin_config)
        assessment_config.logger.info("Building Project Advisor")
        self.project_advisor = ProjectAdvisor(client = client, 
                                             config = assessment_config, 
                                             project = project
                                                 )

        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None
    
    
    def get_style_html(self):
        status = self.project_advisor.get_status()
        if status == "OK":
            color = "green"
        elif status == "WARNING":
            color = "orange"
        elif status == "ERROR":
            color = "red"
        else:
            color = "gray"
        
        style = """
            <style>
                h3.status {{
                  color: {color};
                  font-family: verdana;
                  font-size: 100%;
                }}
                h3.success {{
                  color: green;
                  font-family: verdana;
                  font-size: 100%;
                }}
            </style>
            """.format(color = color)
        return style
    
    def get_checks_df(self):
        check_records = []
        for check in self.project_advisor.checks:
            check_record = {
                                "check_name": check.name,
                                "check_category": check.category.name,
                                "pass": check.check_pass,
                                "message": check.message,
                                "is_critical": check.is_critical
                            }
            check_records.append(check_record)
        return pd.DataFrame.from_dict(check_records)
    
    
    def get_failed_checks_html(self, df):
        check_result_df = df
        failed_check_df = check_result_df[check_result_df["pass"] == False]
        failed_check_df.drop(columns=['pass'], inplace = True)
        nbr_failed_checks = len(failed_check_df.index)
        
        category_tables = ""
        for category in set(failed_check_df["check_category"]):
            cat_df = failed_check_df[failed_check_df["check_category"] == category]
            cat_df.drop(columns=['check_category'], inplace = True)
            
            category_tables += "<h1>{category}</h1>".format(category = category)
            category_tables += cat_df.to_html(index = False)
        
        return category_tables
    
    
    
    def run(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        self.project_advisor.run()
        
        status = self.project_advisor.get_status()
        score = self.project_advisor.get_score()
        checks_df = self.get_checks_df()
        checks_df = checks_df[checks_df["pass"].isin([True, False])]
        
        nbr_failed_critical_checks = list(checks_df[checks_df["pass"] == False]["is_critical"]).count(True)
        nbr_failed_checks = list(checks_df["pass"]).count(False)
        nbr_passed_checks = list(checks_df["pass"]).count(True)
        category_tables = self.get_failed_checks_html(checks_df)
        style = self.get_style_html()
        

        html = """
                <head>
                  {style}
                  <title>PAT Report</title>
                  <h1>PAT Report</h1>
                  <h3>Score : {score}</h2>
                  <h3 class="success"> You have successfully passed {nbr_passed_checks} checks! </h3>
                  <h3 class="status"> We have identified {nbr_failed_checks} improvement with {nbr_failed_critical_checks} critical checks failed </h3>
                  <h3>See the following recommendations</h3>
                </head>
                <body>
                {recommendations}
                </body>
                """.format(score = "{:.2f}%".format(score*100),
                           nbr_failed_checks = nbr_failed_checks,
                           nbr_passed_checks = nbr_passed_checks,
                           nbr_failed_critical_checks = nbr_failed_critical_checks,
                           style = style,
                           recommendations = category_tables)
        

        return html
        