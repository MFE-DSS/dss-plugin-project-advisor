# This file is the actual code for the Python runnable instance-advisor
from dataiku.runnables import Runnable

import dataiku
import dataikuapi
import os, json
import logging

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor
from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        
        client = dataiku.api_client()
        
        # Load component specific parameters
        project_folder_id = config.get("folder_id","")
        check_report_dataset_name = config.get("check_report_dataset",None)
        metric_report_dataset_name = config.get("metric_report_dataset",None)
        
        # Creating Logging connections
        check_report_dataset = dataiku.Dataset(check_report_dataset_name)
        metric_report_dataset = dataiku.Dataset(metric_report_dataset_name)
        
        assessment_config = DSSAssessmentConfigBuilder.build_from_macro_config(config = config, plugin_config = plugin_config)
        
        # KEEP COMMENTED
        #assessment_config.logger.debug(f"config {config}")
        #assessment_config.logger.debug(f"plugin_config {plugin_config}")
        
        self.batch_project_advisor = BatchProjectAdvisor(client = client,
                                                    config = assessment_config, 
                                                    folder_id = project_folder_id,
                                                    check_report_dataset = check_report_dataset,
                                                    metric_report_dataset = metric_report_dataset)
        
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def run(self, progress_callback):
        """
        Run the BatchProjectAdvisor and save the report.
        """
        self.batch_project_advisor.run()
        self.batch_project_advisor.save()
        return f"ALL checks have run\n Overall score : {self.batch_project_advisor.get_score()} \n {[(pa.project.project_key, pa.get_score()) for pa in self.batch_project_advisor.project_advisors]}"
        
        