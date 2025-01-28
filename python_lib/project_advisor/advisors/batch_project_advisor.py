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

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments.config import DSSAssessmentConfig

from project_advisor.advisors import DSSAdvisor
from project_advisor.advisors.project_advisor import ProjectAdvisor



class BatchProjectAdvisor(DSSAdvisor):
    """
    The BatchProjectAdvisor Class runs the ProjectAdvisor on a set of projects.
    """
    project_folder : dataikuapi.dss.projectfolder.DSSProjectFolder
    project_advisors :List[ProjectAdvisor] = None

    def __init__(self,
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 folder_id: str,
                 check_report_dataset : dataiku.Dataset,
                 metric_report_dataset : dataiku.Dataset
    ):

        super().__init__(client = client, 
                         config = config,
                         check_report_dataset = check_report_dataset,
                         metric_report_dataset = metric_report_dataset
                       )

        if len(folder_id) == 0:
            self.project_folder = self.client.get_root_project_folder()
        else:
            self.project_folder = self.client.get_project_folder(folder_id)
            
        self.init_project_advisors()
        
    
    def run_checks(self) -> List[ProjectAdvisor]:
        """
        Run all the project checks over all of the projects.
        """
        self.config.logger.info(f"Running project checks on all the projects")
        [proj_advisor.run_checks() for proj_advisor in self.project_advisors]
        return self.project_advisors
    

    def run_metrics(self) -> List[ProjectAdvisor]:
        """
        Run the project metrics on all of the projects.
        """
        self.config.logger.info(f"Running metrics on all ProjectAdvisors")
        [proj_advisor.run_metrics() for proj_advisor in self.project_advisors]
        return self.project_advisors
    
    def run(self) -> None:
        """
        Run all the metrics and checks for a project.
        """
        [pa.run() for pa in self.project_advisors]
        return
    
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Save the metrics and checks for all the projects
        """
        self.config.logger.info(f"Saving all the metrics and checks for every project")
        
        metrics = []
        checks = []
        for pa in self.project_advisors:
            metrics.extend(pa.metrics)
            checks.extend(pa.checks)
        self.save_metrics(metrics, timestamp = timestamp)
        self.save_checks(checks, timestamp = timestamp)
        return 
  
    def get_score(self) -> float:
        """
        Return the average project score
        """
        return mean([project_advisor.get_score() for project_advisor in self.project_advisors])
    
    def get_project_metric_list(self, metric_name : str) -> List[DSSMetric]:
        
        metric_list = []
        for pa in self.project_advisors:
            for m in pa.metrics:
                if m.name == metric_name:
                    metric_list.append(m)
        return metric_list
    
    def recursive_project_search(self, folder: dataikuapi.dss.projectfolder.DSSProjectFolder) -> List[str]:
        """
        Recursive function to find all projects in a given folder.
        """
        project_keys = []
        project_keys.extend(folder.list_project_keys())
        for child_folder in folder.list_child_folders():
            project_keys.extend(self.recursive_project_search(child_folder))
        return project_keys
            
    def init_project_advisors(self) -> None:
        """
        Finds all the relevant project.
        Build and save a ProjectAdvisor for each project.
        """
        self.config.logger.info(
            f"Creating ProjectAdvisors for every project in the folder : {self.project_folder.get_name()}"
        )
        project_keys = self.recursive_project_search(self.project_folder)
        
        project_advisors = []
        all_check_results = {}
        for project_key in project_keys:
            project = self.client.get_project(project_key)
            proj_advisor = ProjectAdvisor(
                client = self.client, 
                config = self.config, 
                project = project, 
                check_report_dataset = self.check_report_dataset,
                metric_report_dataset = self.metric_report_dataset
            )
            project_advisors.append(proj_advisor)
        self.project_advisors = project_advisors