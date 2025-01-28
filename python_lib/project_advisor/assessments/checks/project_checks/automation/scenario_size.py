import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ScenarioSizeCheck(ProjectCheck):
    """
    Check that the number of steps in a scenario is below a certain threshold.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ScenarioSizeCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.AUTOMATION,
            name="scenario_size_check",
            metrics = metrics
        )

    def get_step_based_scenario_ids(self) -> List[str]:
        """
        Retrieves the IDs of all step-based scenarios in the project.
        :return: self
        """
        scenario_items = self.project.list_scenarios()
        ids = [
            scenario_item["id"]
            for scenario_item in scenario_items
            if scenario_item["type"] == "step_based"
        ]
        return ids

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if any scenarios exceed the maximum number of allowed steps.
        :return: self
        """
        config = self.config.get_config()["check_configs"]
        max_nbr_steps_in_scenarios = config["max_nbr_steps_in_scenarios"]
        step_based_scenario_ids = self.get_step_based_scenario_ids()

        check_pass = True
        message = f"All Scenarios are under the max number of steps : {max_nbr_steps_in_scenarios}"
        result = {}

        if len(step_based_scenario_ids) != 0:
            big_scenarios = []
            for id in step_based_scenario_ids:
                scenario = self.project.get_scenario(id)
                nbr_scenario_steps = len(scenario.get_settings().raw_steps)
                if nbr_scenario_steps > max_nbr_steps_in_scenarios:
                    big_scenarios.append(id)
                    check_pass = False
            if not check_pass:
                message = f"{len(big_scenarios)} scenarios identified with more than {max_nbr_steps_in_scenarios} steps. See : {big_scenarios}."
                result["big_scenarios"] = big_scenarios

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self


