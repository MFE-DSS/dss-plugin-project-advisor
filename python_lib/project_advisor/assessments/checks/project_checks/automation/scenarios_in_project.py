import dataikuapi
from typing import List
from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ProjectHasScenarioCheck(ProjectCheck):
    """
    Checks if the project has at least one scenario.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectHasScenarioCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.AUTOMATION,
            name="project_has_scenario_check",
            metrics = metrics
        )
        
    def check_for_scenarios(self) -> bool:
        """
        Checks if the project has at least one scenario.
        """
        scenarios = self.project.list_scenarios()
        return len(scenarios) > 0
    

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project has at least one scenario.
        :return: self
        """
        check_pass = self.check_for_scenarios()

        if check_pass:
            self.message = "The project has at least one scenario."
            self.run_result = {"scenario_count": len(self.project.list_scenarios())}
        else:
            self.message = "The project has no scenarios."
            self.run_result = {"scenario_count": 0}

        self.check_pass = check_pass
        return self
