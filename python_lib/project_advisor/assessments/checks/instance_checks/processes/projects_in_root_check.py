import dataikuapi
import pandas as pd
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor


class ProjectsInRootCheck(InstanceCheck):
    """
    A class that checks that there are no projects in the DSS root folder.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectsInRootCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics = metrics,
            batch_project_advisor = batch_project_advisor,
            category=InstanceCheckCategory.PROCESSES,
            name="projects_in_root_check",
            description="Checks that there are no projects in the DSS root folder."
        )

    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if there are no projects in the DSS root folder.
        :return: self
        """

        root_folder = self.client.get_root_project_folder()

        check_pass = True
        message = "All projects are in DSS folders"
        result = []

        projects_in_root = []
        for prj in root_folder.list_projects():
            prj_id = prj.get_summary()['projectKey']
            projects_in_root.append(prj_id)

        if len(projects_in_root) > 0:
            check_pass = False
            message = f"{len(projects_in_root)} project(s) is(are) in the DSS root folder"
            result = {"projects_in_root": projects_in_root}

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self