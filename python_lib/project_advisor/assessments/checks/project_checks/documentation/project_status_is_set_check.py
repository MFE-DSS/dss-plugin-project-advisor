import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck




class ProjectStatusIsSetCheck(ProjectCheck):
    """
    A class to check if a project's status is set in Dataiku DSS.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectStatusIsSetCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="project_status_is_set_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project's status is set.
        :return: self
        """
        check_pass = True
        message = "This project has its status set."
        result = {}

        project_status = ""
        project_summary = self.project.get_summary()
        project_key = project_summary["projectKey"]

        if "projectStatus" in project_summary:
            project_status = project_summary["projectStatus"]
        else:
            check_pass = False
            message = "This project does not have its status set"

        result["project_key"] = project_key
        result["project_status"] = project_status
        
        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self