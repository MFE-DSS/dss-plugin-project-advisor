import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class MainScenarioExistsCheck(ProjectCheck):
    """
    Check that the project has a main scenario that is configured appropriately.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics: List[DSSMetric],
    ):
        """
        Initializes the MainScenarioExistsCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.AUTOMATION,
            name="main_scenario_exists_check",
            metrics=metrics,
            description="Checks that the project has a scenario with the 'Scenario Type:main' tag and that scenario has a trigger and a reporter"
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
        Runs the check to determine if the project has a main scenario that is configured appropriately.
        :return: self
        """

        check_pass = False
        message = "This project does not have a scenario tagged as 'main'."
        result = {}

        if self.main_scenario_tag_exists():

            scenarios = self.project.list_scenarios(as_type="objects")
            for s in scenarios:
                s_raw_settings = s.get_settings().get_raw()
                s_tags = s_raw_settings["tags"]
                if any("Scenario Type:main" in tag for tag in s_tags):
                    if len(s_raw_settings["triggers"]) == 0:
                        message = "Found a scenario tagged as 'main' but no triggers have been set."
                    elif len(s_raw_settings["reporters"]) == 0:
                        message = "Found a scenario tagged as 'main' but no reporters have been set."
                    else:
                        check_pass = True
                        message = "Found a scenario tagged as 'main' that is configured with a trigger and a reporter."
                        break
        else:
            message = "Could not find the global tag 'Scenario Type:main'."

        self.check_pass = check_pass
        self.message = message
        self.run_result = result

        return self