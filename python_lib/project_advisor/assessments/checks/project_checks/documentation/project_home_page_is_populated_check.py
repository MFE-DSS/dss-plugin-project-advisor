import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck




class ProjectHomePageIsPopulatedCheck(ProjectCheck):
    """
    A class to check if a project's home page is populated in Dataiku DSS.

    :param client: The DSS client instance.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics = List[DSSMetric]
    ):
        """
        Initializes the ProjectHomePageIsPopulatedCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="project_home_page_is_populated_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project's home page is populated.
        :return: self
        """
        check_pass = True
        message = ""
        result = {}

        project_summary = self.project.get_summary()
        project_key = project_summary["projectKey"]

        if "shortDesc" in project_summary and project_summary["shortDesc"] != "":
            result["short_description"] = project_summary["shortDesc"]
        else:
            check_pass = False
            result["short_description"] = ""
            message += "This project does not have a short description."

        if "description" in project_summary and project_summary["description"] != "":
            result["long_description"] = project_summary["description"]
        else:
            check_pass = False
            result["long_description"] = ""
            message += "This project does not have a long description."

        if check_pass:
            message = "This project has its home page populated."

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self