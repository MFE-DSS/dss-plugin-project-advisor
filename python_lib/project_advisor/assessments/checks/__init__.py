import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

from project_advisor.assessments.dss_assessment import DSSAssessment
from project_advisor.assessments.config import DSSAssessmentConfig 
from project_advisor.assessments.metrics import DSSMetric

class DSSCheck(DSSAssessment):
    """
    Abstract base class for DSS checks.
    """
    check_pass : bool = None
    is_critical = False
    message : str = None
    metrics : List[DSSMetric] = None
        
    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        name: str,
        metrics : List[DSSMetric],
        description: str = "",
        dss_version_min = None,
        dss_version_max = None,
    ):

        super().__init__(client = client, 
                         config = config,
                         name = name,
                         description = description,
                         dss_version_min = dss_version_min,
                         dss_version_max = dss_version_max)
        self.metrics = metrics
        
        self.set_criticality()
        
    def set_criticality(self) -> None:
        """
        Set the is_critical flag for the check based on the critical_project_check_list.
        """
        config = self.config.get_config()
        print (f"config : {config}")
        critical_project_check_list = config.get("check_configs", {}).get("critical_project_check_list", [])
        
        if self.name in critical_project_check_list:
            self.is_critical = True
        
    @abstractmethod
    def run(self) -> Self:
        """
        Abstract method to run the check then save and return the result.
        """
        return
    
    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["check_pass"] = self.check_pass
        metadata["is_critical"] = self.is_critical
        return metadata
    
    def get_metric(self, metric_name : str) -> DSSMetric:
        """
        Function to use in a check to run get a previously computed metric object.
        """
        for m in self.metrics:
            if m.name == metric_name:
                return m
        return None
    
    def get_lc_model(self, llm_id, temperature):
        """
        Return langchain model from llm_id regardless of DSS version
        """
        
        dss_version = Version(self.client.get_instance_info()._data["dssVersion"])
        dss_13_1_0 = Version("13.1.0")
        if dss_version >= dss_13_1_0:
            model = self.project.get_llm(llm_id).as_langchain_llm()
            model.temperature = temperature
            return model
        else:
            from dataiku.langchain.dku_llm import DKUChatLLM
            return DKUChatLLM(llm_id=llm_id, temperature=temperature)


    

