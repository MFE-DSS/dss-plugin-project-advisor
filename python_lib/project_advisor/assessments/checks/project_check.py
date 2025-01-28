import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version


from dataikuapi.dss.flow import DSSProjectFlowGraph


from project_advisor.assessments.dss_assessment import DSSAssessment
from project_advisor.assessments.checks import DSSCheck
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.metrics import DSSMetric

class ProjectCheck(DSSCheck):
    """
    A class representing a project check.
    """

    project: dataikuapi.dss.project.DSSProject = None
    category: ProjectCheckCategory = None

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        category: ProjectCheckCategory,
        name: str,
        metrics : List[DSSMetric] = [],
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
        self.project = project
        self.category = category

    def get_assessment_type(self) -> str:
        """
        Method to get the type of assessment
        """
        return "ProjectCheck"
    
    def filter(self, filter_config : dict) -> bool:
        """
        Method filter out Project Checks Assessments
        """
        # Filter by project check category
        remove = super().filter(filter_config)
        if "project_check_categories" in filter_config.keys():
            if self.category not in filter_config["project_check_categories"]:
                remove = True
                
        # Filter by check name (white list)
        if filter_config.get("use_project_check_white_list", False):
            project_check_white_list = filter_config.get("project_check_white_list", [])
            if self.name not in project_check_white_list:
                remove = True

        return remove
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        metadata = super().get_metadata()
        metadata.update(
            {"project_key": self.project.project_key, "category": self.category.name}
        )
        return metadata

    def count_datasets_in_graph(self, graph: DSSProjectFlowGraph):
        nodes = graph.nodes
        count = len([name for name in nodes.keys() if "DATASET" in nodes[name]["type"]])
        return count

    def get_output_dataset_ids(self, graph: DSSProjectFlowGraph) -> list:
        """
        Retrieves the IDs of output datasets in the project's flow.
        """
        nodes = graph.nodes
        output_dataset_ids = []

        for node_id in nodes.keys():
            if (
                "DATASET" in nodes[node_id]["type"]
                and len(nodes[node_id]["successors"]) == 0
            ):
                output_dataset_ids.append(nodes[node_id]["ref"])

        return output_dataset_ids
