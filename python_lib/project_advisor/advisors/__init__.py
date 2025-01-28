import dataikuapi
import dataiku
from typing import List, Any
from abc import ABC, abstractmethod
from types import ModuleType
from pathlib import Path
import os
import importlib
import sys, inspect
import pandas as pd
import json

from datetime import datetime
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.dss_assessment import DSSAssessment
from project_advisor.assessments.metrics import DSSMetric

from project_advisor.assessments.checks import DSSCheck

class DSSAdvisor(ABC):
    """
    An abstract base class for computing metrics and checks on DSS.
    """

    client: dataikuapi.dssclient.DSSClient = None
    config: DSSAssessmentConfig = None
    metrics : List[DSSMetric] = None
    checks : List[DSSCheck] = None
    check_report_dataset : dataiku.Dataset = None
    metric_report_dataset : dataiku.Dataset = None

    def __init__(self, 
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 check_report_dataset : dataiku.Dataset,
                 metric_report_dataset : dataiku.Dataset
                ):
        """
        Initializes the DSSAdvisor with the provided client and configuration.
        """
        self.client = client
        self.config = config
        self.check_report_dataset = check_report_dataset
        self.metric_report_dataset = metric_report_dataset


    @abstractmethod
    def run_metrics(self, timestamp : datetime) -> List[DSSMetric]:
        """
        Abstract method to run all metrics and return the Metrics.
        """
        return
  
    @abstractmethod
    def run_checks(self, timestamp : datetime) -> List[DSSCheck]:
        """
        Abstract method to run all checks and return the Checks.
        """
        return

    @abstractmethod
    def run(self) -> None:
        """
        Abstract method to run all the metrics and checks.
        """
        return
    
    @abstractmethod
    def get_score(self) -> float:
        """
        Abstract method to compute the score overall score of the advisor.
        """
        return
    
    @abstractmethod
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Abstract method to save all the checks to a dataset in the flow.
        """
        return
    
    def format_ts(self, timestamp : datetime):
        """
        Format timestamp to act as the ID of the Assessment.
        """
        return timestamp.strftime("%m/%d/%Y, %H:%M:%S")
    
    def safe_json_to_str(self, data : dict) -> str:
        try:
            return json.dumps(data)
        except Exception as error:
            return str(error)
    
    def save_metrics(self, metrics : List[DSSMetric], timestamp : datetime) -> None:
        """
        Method to save the metrics to a logging dataset in the flow.
        """
        self.init_metric_logging_dataset()
        
        ts_str = self.format_ts(timestamp)
        metric_records = []
        for metric in metrics:
            project_key = ""
            if metric.get_assessment_type() == "ProjectMetric":
                project_key = metric.project.get_settings().project_key
            metric_record = {
                    "timestamp": ts_str,
                    "metric_name": metric.name,
                    "metric_value": metric.value,
                    "metric_type" : metric.metric_type.name,
                    "project_id": project_key,
                    "result_data": self.safe_json_to_str(metric.get_metadata()),
                }
            self.config.logger.debug(f"[metric_record]{json.dumps(metric_record)}") # Logging report metric to job logs
            metric_records.append(metric_record)
        new_metrics_df = pd.DataFrame.from_dict(metric_records)
        
        
        new_log_df = pd.concat([self.metric_report_dataset.get_dataframe(), new_metrics_df])
        self.metric_report_dataset.write_with_schema(new_log_df)
        return
    

    def save_checks(self,checks : List[DSSCheck], timestamp : datetime) -> None:
        """
        Method to save all the checks to a logging dataset in the flow.
        """
        self.config.logger.debug(f"saving {len(checks)} checks")
        self.init_check_logging_dataset()
        

        ts_str = self.format_ts(timestamp)
        check_records = []
        for check in checks:
            project_key = ""
            if check.get_assessment_type() == "ProjectCheck":
                project_key = check.project.get_settings().project_key
            
            check_record = {
                                "timestamp": ts_str,
                                "check_name": check.name,
                                "check_category": check.category.name,
                                "project_id": project_key,
                                "pass": check.check_pass,
                                "message": check.message,
                                "result_data": self.safe_json_to_str(check.get_metadata()),
                            }
            
            self.config.logger.debug(f"[check_record]{json.dumps(check_record)}") # Logging report metric to job logs
            check_records.append(check_record)

        new_checks_df = pd.DataFrame.from_dict(check_records)
        new_log_df = pd.concat([self.check_report_dataset.get_dataframe(), new_checks_df])
        self.check_report_dataset.write_with_schema(new_log_df)
        return
    

    def init_metric_logging_dataset(self) -> None:
        """
        Init the metric logging dataset if empty or if there is no data.
        """
        
        df_init = pd.DataFrame(
            {
                "timestamp": pd.Series(dtype="str"),
                "metric_name": pd.Series(dtype="str"),
                "metric_value": pd.Series(dtype="str"),
                "metric_type": pd.Series(dtype="str"),
                "project_id": pd.Series(dtype="str"),
                "result_data": pd.Series(dtype="str"),
            }
        )
        try:
            self.metric_report_dataset.get_dataframe()
        except:
            self.metric_report_dataset.write_schema_from_dataframe(df_init)
            self.metric_report_dataset.write_from_dataframe(df_init)
        return
    
    def init_check_logging_dataset(self) -> None:
        """
        Init the check logging dataset if empty or if there is no data.
        """
        df_init = pd.DataFrame(
            {
                "timestamp": pd.Series(dtype="str"),
                "check_name": pd.Series(dtype="str"),
                "check_category": pd.Series(dtype="str"),
                "project_id": pd.Series(dtype="str"),
                "pass": pd.Series(dtype="bool"),
                "message": pd.Series(dtype="str"),
                "result_data": pd.Series(dtype="str"),
            }
        )
        try:
            self.check_report_dataset.get_dataframe()
        except:
            self.check_report_dataset.write_schema_from_dataframe(df_init)
            self.check_report_dataset.write_from_dataframe(df_init)
        return
    
    def fetch_built_in_and_add_on_classes(self, root_module : ModuleType, module_class : ModuleType) -> List[ModuleType]:
        """
        Find all the built-in and add on module_class sub classes.
        This requires the macro to be impersonated.
        """
        built_in_classes = self.fetch_classes(root_module, module_class)
        add_on_classes = self.fetch_add_on_classes(module_class)
        #self.config.logger.debug(f"module_name : {module_class.__name__}")
        #self.config.logger.debug(f"built_in_classes : {built_in_classes}")
        #self.config.logger.debug(f"add_on_classes : {add_on_classes}")
        return built_in_classes + add_on_classes

    def fetch_add_on_classes(self, module_class : ModuleType) -> List[ModuleType]:
        """
        Find all the module_class sub classes within the default project lib.
        """
        try:
            self.client = dataiku.api_client()
            project_key = self.client.get_default_project().project_key
            dataDirPath = self.client.get_instance_info().raw["dataDirPath"]
            proj_py_lib_root = dataDirPath + f"/config/projects/{project_key}/lib/python"
            
            #self.config.logger.debug(f"proj_py_lib_root : {proj_py_lib_root}")
            
            sys.path.append(proj_py_lib_root)
            import pat_custom_assessments
            
            classes = self.fetch_classes(pat_custom_assessments, module_class)
            return classes
        except Exception as error:
            # Case were no custom assessments have been provided in the "pat_custom_assessments" Folder.
            self.config.logger.debug(f"Failed to load add on classes : {str(error)}")
            return []
    
    
    def fetch_classes(self, root_module : ModuleType, module_class : ModuleType) -> List[ModuleType]:
        """
        Find all the module_class sub classes within a root_module.
        """
        module_folder_root = Path(root_module.__path__[0])
        base_module_name = root_module.__name__

        modules = []
        for root, subFolder, files in os.walk(module_folder_root):
            for item in files:
                if item.endswith(".py") and item != "__init__.py":
                    path = Path(root, item)
                    rel_path = path.relative_to(module_folder_root)
                    module_name = (
                        base_module_name
                        + "."
                        + rel_path.as_posix()[:-3].replace("/", ".")
                    )
                    module = importlib.import_module(module_name, package=None)
                    modules.append(module)

        classes = []
        for module in modules:
            for _, check_class in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(check_class, module_class)
                    and module_class != check_class
                ):
                    classes.append(check_class)
        return classes
    
    def filter_assessments(self, assessments : List[DSSAssessment]) -> List[DSSAssessment]:
        """
        Filter DSSAssessment based on the DSSAssessmentConfig and Class parameters.
        """
        self.config.logger.debug(f"assessments before all filtering : {len(assessments)}")
        
        if len(assessments)==0:
            return assessments
        
        # Load filters
        filter_config = self.config.get_config().get("check_filters",{})
        
        # Run filtering all all assessments
        filtered_assessments = [assessment for assessment in assessments if not assessment.filter(filter_config)]

        return filtered_assessments
