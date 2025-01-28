import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from types import ModuleType
from abc import ABC, abstractmethod
from datetime import datetime
import json
import sys, inspect
import logging
from pathlib import Path
import os
import importlib
from statistics import mean 

from project_advisor.advisors import DSSAdvisor
from project_advisor.assessments.config import DSSAssessmentConfig

from project_advisor.assessments.checks.project_check import ProjectCheck
from project_advisor.assessments.metrics.project_metric import ProjectMetric

import project_advisor.assessments.checks.project_checks # for loading
import project_advisor.assessments.metrics.project_metrics # for loading

class ProjectAdvisor(DSSAdvisor):
    """
    The project Advisor Class runs project checks on a given project.
    Before each run, the checks are filtered according the the DSSAssessmentConfigs.
    The result of the project assessments can be logged to a logging dataset.
    """

    project: dataikuapi.dss.project.DSSProject
    def __init__(self,
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 project: dataikuapi.dss.project.DSSProject,
                 check_report_dataset : dataiku.Dataset = None,
                 metric_report_dataset : dataiku.Dataset = None
    ):
        
        super().__init__(client = client, 
                         config = config,
                         check_report_dataset = check_report_dataset,
                         metric_report_dataset = metric_report_dataset
                       )
        self.project = project
        
        self.init_project_metric_list()
        self.init_project_check_list()
    
    
    def run_metrics(self) -> List[ProjectMetric]:
        """
        Run all available metrics.
        Note : Do not run directly, use the *run* function instead.
        """
        self.config.logger.debug(f"Running Project Metrics for project {self.project.project_key}")

        [metric.safe_run() for metric in self.metrics]

        return self.metrics
    
    def run_checks(self) -> List[ProjectCheck]:
        """
        Run all available checks.
        Note : The metrics should be run before running all the checks.
        Note : Do not run directly, use the *run* function instead.
        """
        self.config.logger.info(f"Running Project Checks for project {self.project.project_key}")
        
        if self.metrics == None:
            raise Exception('Run project metrics before running project checks')

        [check.safe_run() for check in self.checks]
        
        return self.checks

    def run(self) -> None:
        """
        Run all the availalbe metrics and checks for a project.
        """
        self.run_metrics()
        self.run_checks()
        return
    
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Save all the checks and metrics for this ProjectAdvisor
        """
        self.save_metrics(self.metrics, timestamp = timestamp)
        self.save_checks(self.checks, timestamp = timestamp)
        return
          
    def get_status(self) -> str:
        """
        Compute the project status.
        This will be based on the critical checks.
        """
        status = "OK" # Case where all the checks have passed
        # check for Warning
        if self.get_score() < 1: # Case where there are no critical checks that failed.
            status = "WARNING"
        
        # Check for Criticality
        for check in self.checks: 
            if check.is_critical:
                if not check.check_pass: # Case where a critical check has failed.
                    status = "ERROR" 
        return status
        
        
    def get_score(self) -> float:
        """
        Compute the project score.
        The Project score is the ratio between the passed checks and the overall relevant checks.
        """
        
        # Case where the checks have never been run
        if self.checks == None:
            raise Exception('Run project checks before computing the project score')
        
        self.config.logger.info(f"Computing project score : {self.project.project_key}")
        
        failed_checks = len([check_result for check_result in self.checks if check_result.check_pass == False])
        passed_checks =  len([check_result for check_result in self.checks if check_result.check_pass == True])
        self.config.logger.info(f"passed_checks : {passed_checks}")
        self.config.logger.info(f"failed_checks : {failed_checks}")
        
        # Case where not one check is applicable.
        if (failed_checks + passed_checks) ==0:
            return 1
        
        return passed_checks/(failed_checks + passed_checks)        
    
    def init_project_metric_list(self) -> None:
        """
        Load all the ProjectMetric Classes under the metrics/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        self.config.logger.info(f"Building full list of metrics for project {self.project.project_key}")
        
        # Load all the Project Metrics classes 
        project_metric_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.metrics.project_metrics,
                                                                       module_class = ProjectMetric)
        # Instantiate all the project metrics
        all_metrics = []
        for project_metric_class in project_metric_classes:
            all_metrics.append(project_metric_class(client = self.client, 
                                                  config = self.config, 
                                                  project = self.project))

        # Filter all the checks according the assessment config & save
        self.metrics = self.filter_assessments(all_metrics)
        return
  
    def init_project_check_list(self) -> None:
        """
        Load all the ProjectCheck Classes under the checks/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        self.config.logger.info(
            f"Building full list of checks for project {self.project.project_key}"
        )

        # Load all the Project Check classes 
        project_check_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.checks.project_checks,
                                                   module_class = ProjectCheck)
        # Instantiate all the project checks
        all_checks = []
        for project_check_class in project_check_classes:
            all_checks.append(project_check_class(client = self.client, 
                                                  config = self.config, 
                                                  project = self.project,
                                                  metrics = self.metrics))
        self.config.logger.info(
            f"All Checks list is {all_checks}"
        )
        # Filter all the checks according the assessment config & save
        self.checks = self.filter_assessments(all_checks)
        return
