# This file is the actual code for the Python runnable instance-advisor
from dataiku.runnables import Runnable

import dataiku
import dataikuapi
import os, json
import logging

from project_advisor.advisors.instance_advisor import InstanceAdvisor
from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        print(f"Recieved Runnable configs is {config}")
        
        client = dataiku.api_client()
        
        # Load component specific parameters
        check_report_dataset_name = config.get("check_report_dataset",None)
        metric_report_dataset_name = config.get("metric_report_dataset",None)
        
        # Creating Logging connections
        check_report_dataset = dataiku.Dataset(check_report_dataset_name)
        metric_report_dataset = dataiku.Dataset(metric_report_dataset_name)
        
        
        assessment_config = DSSAssessmentConfigBuilder.build_from_macro_config(config = config, plugin_config = plugin_config)
        
        # KEEP COMMENTED
        #assessment_config.logger.debug(f"config {config}")
        #assessment_config.logger.debug(f"plugin_config {plugin_config}")
        
        assessment_config.logger.info(f"Runnable instantating instance advisor")
        self.instance_advisor = InstanceAdvisor(client = client,
                                                config = assessment_config, 
                                                check_report_dataset = check_report_dataset,
                                                metric_report_dataset = metric_report_dataset)
        
        assessment_config.logger.info(f"Macro sucessfully instantiated instance advisor")
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

        
    def run(self, progress_callback):
        """
        Run the Instance advisor and save the report.
        """
        self.instance_advisor.run()
        self.instance_advisor.save()

        return f"ALL checks have run\n Overall score : {self.instance_advisor.get_score()}"
        
        