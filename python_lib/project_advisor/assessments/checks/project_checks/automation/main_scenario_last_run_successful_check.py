import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class MainScenarioLastRunSuccessfulCheck(ProjectCheck):
    """
    Check that the main scenario's last run was successful.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the MainScenarioLastRunSuccessfulCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.AUTOMATION,
            name="main_scenario_last_run_successful_check",
            metrics=metrics,
            description="Check that the main scenario's last run was successful."
        )

    def main_scenario_tag_exists(self) -> bool:
        """
        Checks that there is a global tag category named 'Scenario Type' that has the tag 'main'.
        :return: boolean
        """
        global_tags = self.client.get_general_settings().get_raw()["globalTagsCategories"]
        if (
            len(global_tags) != 0
            and any(tag["name"] == "Scenario Type" for tag in global_tags)
            and any(tag["name"] == "main" for cat in global_tags for tag in cat["globalTags"])
        ):
            return True
        return False

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the main scenario's last run was successful.
        :return: self
        """
        check_pass = False
        message = "This project does not have a scenario tagged as 'main'."
        result = {}

        if self.main_scenario_tag_exists():
            scenarios = self.project.list_scenarios(as_type="objects")
            for s in scenarios:
                if any("Scenario Type:main" in tag for tag in s.get_settings().get_raw()["tags"]):
                    try:
                        if s.get_last_finished_run().outcome == "SUCCESS":
                            check_pass = True
                            message = "This project's main scenario had a successful last run."
                    except:
                        message = "This project's main scenario does not have a completed run."
                    break
        else:
            message = "Could not find the global tag 'Scenario Type:main'."

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self