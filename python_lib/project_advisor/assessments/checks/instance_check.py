import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

import dataikuapi

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor
from project_advisor.assessments.checks import DSSCheck 
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.metrics.instance_metric import InstanceMetric

class InstanceCheck(DSSCheck):
    """
    A class representing a Instance check.
    """

    category: InstanceCheckCategory = None
    batch_project_advisor :BatchProjectAdvisor = None

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[InstanceMetric],
        category: InstanceCheckCategory,
        name: str,
        description: str = "",
        dss_version_min: Version = None,
        dss_version_max: Version = None
    ):

        super().__init__(client = client,
                         config = config,
                         name = name,
                         metrics = metrics,
                         description = description,
                         dss_version_min = dss_version_min,
                         dss_version_max = dss_version_max)
        
        self.category = category
        self.batch_project_advisor = batch_project_advisor
        
    def get_assessment_type(self) -> str:
        """
        Method to get the type of assessment
        """
        return "InstanceCheck"
    
    def filter(self, filter_config : dict) -> bool:
        """
        Method filter out Instance Checks Assessments
        """
        
        remove = super().filter(filter_config)
        if "instance_check_categories" in filter_config.keys():
            if self.category not in filter_config["instance_check_categories"]:
                remove = True

        return remove
    
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        metadata = super().get_metadata()
        metadata.update(
                {"project_key": "", "category": self.category.name}
            )
        return metadata