import dataikuapi


from typing import Any, Dict, List
from typing_extensions import Self
from abc import ABC, abstractmethod

from packaging.version import Version

from project_advisor.assessments.config import DSSAssessmentConfig


class DSSAssessment(ABC):
    """
    Abstract base class for DSS metrics & checks.
    An Assessment:
    -> Has a unique name & description.
    -> Can be run.
    -> Shares a config with all other Assessments.
    -> Saves it's latest run results.
    -> Has a compatible DSS version range (None meaning no limit)
    -> Has class parameters that can be used for filtering.
    """

    client: dataikuapi.dssclient.DSSClient = None
    config : DSSAssessmentConfig = None
    name: str = None
    description: str = None
    dss_version_min: Version = Version("12.0.0")
    dss_version_max: Version = None
    
    # Filter Params
    has_llm = False
    uses_fs = False
    uses_plugin_usage = False
        
    run_result: dict = None

    def __init__(
        self, 
        client: dataikuapi.dssclient.DSSClient, 
        config : DSSAssessmentConfig,
        name: str,
        description: str = "",
        dss_version_min = None,
        dss_version_max = None
    ):
        """
        Initializes a DSS Assessment with the provided parameters.
        """
        self.client = client
        self.config = config
        self.name = name
        self.description = description
        if dss_version_min is not None:
            self.dss_version_min = dss_version_min
        if dss_version_max is not None:
            self.dss_version_max = dss_version_max

    @abstractmethod
    def run(self) -> Self:
        """
        Abstract method to run an assessment.
        Save an assessment & return the result of an assessment.
        """
        return self
    
    
    def safe_run(self) -> Self:
        """
        Method to run an assessment catching any errors
        """
        try:
            self.run()
        except Exception as error:
            error_dict = {
                            "error" : type(error).__name__,
                            "error_message" : str(error)
                         }
            if isinstance(self.run_result, dict):
                self.run_result.update()
            else:
                self.run_result = error_dict
        return self
    
    @abstractmethod
    def get_assessment_type(self) -> str:
        """
        Abstract method to get the type of assessment (needed for fixing cyclical dependencies)
        """
        return
    

    def filter(self, filter_config : dict) -> bool:
        """
        Method to find if an assessment should be filtered (removed) or not.
        """
        # Filter on DSS version assessment compatibility
        remove = False
        if not self.dss_version_in_range():
            remove = True
            self.config.logger.debug(f"The DSS instance version is not the DSS version range of assessment : {self.name}")
           
        # uses LLM filter : Filter out all llm powered assessments if the llm option is not enabled.
        if "use_llm" in filter_config.keys() and (not filter_config["use_llm"]):
            if self.has_llm == True:
                remove = True
                self.config.logger.debug(f"Assessment {self.name} filtered because it uses an LLM")
        
        # uses plugin filter : Filter all assessments that leverage plugin usage
        if "use_plugin_usage" in filter_config.keys() and (not filter_config["use_plugin_usage"]):
            if self.uses_plugin_usage == True:
                remove = True
                self.config.logger.debug(f"Assessment {self.name} filtered because it leverages plugin usage")
        
        # uses FS filter : Filter all assessments that leverage the DS File System
        if "use_fs" in filter_config.keys() and (not filter_config["use_fs"]):
            if self.uses_fs == True:
                remove = True
                self.config.logger.debug(f"Assessment {self.name} filtered because it leverages the DSS FS")

        return remove
    
    
    def dss_version_in_range(self):
        dss_version = Version(self.client.get_instance_info().raw["dssVersion"])   
        return (dss_version >= self.dss_version_min) and (self.dss_version_max is None or dss_version <= self.dss_version_max)
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        return {
                    "name": self.name,
                    "description" : self.description,
                    "dss_version_min" :str(self.dss_version_min),
                    "dss_version_max" : str(self.dss_version_max),
                    "run_result" : self.run_result,
               }