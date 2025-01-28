import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck




class ProjectHasWikiCheck(ProjectCheck):
    """
    A class used to check if a project has a wiki page in Dataiku DSS.

    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectHasWikiCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="project_has_wiki_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project has a wiki page.
        :return: self
        """
        check_pass = True
        message = "This Project has a wiki"
        result = {}

        if len(self.project.get_wiki().list_articles()) == 0:
            message = "This Project does not have a wiki"
            check_pass = False

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self