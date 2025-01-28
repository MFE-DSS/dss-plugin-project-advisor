import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from abc import ABC, abstractmethod
from datetime import datetime
import json
import sys, inspect
import logging
from pathlib import Path
import os
import importlib


from project_advisor.advisors import DSSAdvisor
from project_advisor.assessments.config import DSSAssessmentConfig

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.checks.instance_check import InstanceCheck

import project_advisor
import project_advisor.assessments.checks.instance_checks # for loading
import project_advisor.assessments.metrics.instance_metrics # for loading


class InstanceAdvisor(DSSAdvisor):
    """
    The Instance Advisor Class runs Instance checks on a given DSS instance.
    Before each run, the checks are filtered according the the DSSAssessmentConfig.
    The result of the assessments can be logged to logging datasets.
    """
    batch_project_advisor: BatchProjectAdvisor = None

    def __init__(self,
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 check_report_dataset : dataiku.Dataset,
                 metric_report_dataset : dataiku.Dataset
    ):

        super().__init__(client = client, 
                         config = config,
                         check_report_dataset = check_report_dataset,
                         metric_report_dataset = metric_report_dataset
                       )

        
        try:
            self.batch_project_advisor = BatchProjectAdvisor(client=client,
                                                             config=config, 
                                                             folder_id="",
                                                             check_report_dataset=check_report_dataset,
                                                             metric_report_dataset=metric_report_dataset)
            self.config.logger.info("BatchProjectAdvisor successfully created")
        except Exception as e:
            self.config.logger.error(f"Failed to create BatchProjectAdvisor: {e}")
            self.batch_project_advisor = None
            
        self.init_instance_metric_list()
        self.init_instance_check_list()

        
    def run_metrics(self) -> List[InstanceMetric]:
        """
        Run all available instance metrics.
        Note : Do not run directly, use the *run* function instead.
        """
        self.config.logger.info(f"Running Instance Metrics")

        [metric.safe_run() for metric in self.metrics]
        
        return self.metrics
    
    def run_checks(self) -> List[InstanceCheck]:
        """
        Run all available instance checks.
        Note : The metrics should be run before running all the checks.
        Note : Do not run directly, use the *run* function instead.
        """
        self.config.logger.info(f"Running Instance Checks")
        
        if self.metrics == None:
            raise Exception('Run project metrics before running project checks')

        [check.safe_run() for check in self.checks]
        
        return self.checks

    def run(self) -> None:
        """
        Run all the available metrics and checks for all projects and the instance.
        """
        
        self.batch_project_advisor.run()
        self.config.logger.debug(f"Sucessfully ran Batch Project Advisor")
        
        self.run_metrics()
        self.config.logger.debug(f"Successfully ran Instance Metrics")
        
        self.run_checks()
        self.config.logger.debug(f"Successfully ran Instance Checks")
        return
    
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Save all the checks and metrics for this ProjectAdvisor
        """
        
        self.batch_project_advisor.save(timestamp = timestamp)
        self.config.logger.info(f"Successfully saved Project Metrics and checks")
        
        self.save_metrics(self.metrics, timestamp = timestamp)
        self.config.logger.info(f"Successfully saved Instance Metrics")
        
        self.save_checks(self.checks, timestamp = timestamp)
        self.config.logger.info(f"Successfully saved Instance Checks")
        
        return
            
    def get_score(self) -> float:
        """
        Compute the project score.
        The Project score is the ratio between the passed checks and the overall relevant checks.
        """
        
        # Case where the checks have never been run
        if self.checks == None:
            raise Exception('Run instance checks before computing the project score')
        
        self.config.logger.info(f"Computing Instance score")
        
        failed_checks = len([check_result for check_result in self.checks if check_result.check_pass == False])
        passed_checks =  len([check_result for check_result in self.checks if check_result.check_pass == True])
        self.config.logger.info(f"passed_checks : {passed_checks}")
        self.config.logger.info(f"failed_checks : {failed_checks}")
        
        # Case where not one check is applicable.
        if (failed_checks + passed_checks) ==0:
            return 1
        
        return passed_checks/(failed_checks + passed_checks)        
    
    def init_instance_metric_list(self) -> None:
        """
        Load all the ProjectMetric Classes under the metrics/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        self.config.logger.info(f"Building full list of metrics for the instance")
        
        # Load all the Intance Metric classes 
        instance_metric_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.metrics.instance_metrics,
                                                                           module_class = InstanceMetric)
        # Instantiate all the Instancemetrics
        all_metrics = []
        self.config.logger.info(f"Building full list of metrics for the instance")
        for instance_metric_class in instance_metric_classes:
            all_metrics.append(instance_metric_class(client = self.client, 
                                                     config = self.config,
                                                     batch_project_advisor = self.batch_project_advisor
                                                    ))
            
        self.config.logger.info(f"Successfuly built full list of metrics for the instance")
        # Filter all the checks according the assessment config & save
        self.metrics = self.filter_assessments(all_metrics)
        return
  
    def init_instance_check_list(self) -> None:
        """
        Load all the ProjectCheck Classes under the checks/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        self.config.logger.info(
            f"Building full list of checks for instance"
        )

        # Load all the Instance Check classes 
        instance_check_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.checks.instance_checks,
                                                                       module_class = InstanceCheck)
        self.config.logger.info(
                f"Instance check classes {instance_check_classes}"
            )
        # Instantiate all the Instance Checks
        all_checks = []
        for instance_check_class in instance_check_classes:
            
            self.config.logger.info(
                f"Instance check class {instance_check_class}"
            )
            all_checks.append(instance_check_class(client = self.client, 
                                                  config = self.config,
                                                  batch_project_advisor = self.batch_project_advisor,
                                                  metrics = self.metrics))
        self.config.logger.info(
            f"All Checks list is {all_checks}"
        )
        # Filter all the checks according the assessment config & save
        
        self.checks = self.filter_assessments(all_checks)
        self.config.logger.info(
                f"Instance check classes are filtering {self.checks}"
            )
        return

     
    