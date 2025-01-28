# File to contain the DSSMetric, DSSProjetMetric & DSSInstanceMetric classes.

import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

from project_advisor.assessments.metrics import (DSSMetric, AssessmentMetricType)
from project_advisor.assessments.config import DSSAssessmentConfig 


class ProjectMetric(DSSMetric):
    """
    An abstract class to run and store Project specific DSS metric computations
    """
    project : dataikuapi.dss.project.DSSProject = None
     
    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config : DSSAssessmentConfig,
        project : dataikuapi.dss.project.DSSProject,
        name: str,
        metric_type : AssessmentMetricType,
        description: str = "",
        dss_version_min = None,
        dss_version_max = None,
    ):

        super().__init__(client = client, 
                         config = config,
                         name = name,
                         metric_type = metric_type,
                         description = description,
                         dss_version_min = dss_version_min,
                         dss_version_max = dss_version_max)
        self.project = project
    

    def get_assessment_type(self) -> str:
        """
        Method to get the type of assessment
        """
        return "ProjectMetric"
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        metadata = super().get_metadata()
        metadata.update(
            {"project_key": self.project.project_key}
        )
        return metadata
    
    @abstractmethod
    def run() -> Self:
        """
        Abstract method to run a project metric.
        Saves the result of a metric run & return the result of a metric run.
        """
        return

        