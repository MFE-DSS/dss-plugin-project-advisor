import dataikuapi
from typing import List
import datetime
from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class FailingActiveScenarioWithTriggerOnDesignCheck(ProjectCheck):
    """
    Checks if any active scenarios with a trigger have failled in the last 7 days on the design node
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the FailingActiveScenarioWithTriggerCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.AUTOMATION,
            name="failing_scenario_with_trigger_design_node_check",
            metrics = metrics
        )
        
    def check_for_active_scenario_triggers(self, scenario) -> bool:
        """
        Checks if a scenario is both active and has an automated trigger set up
        """
        scenario_details = scenario.get_settings().get_raw()
        if (scenario_details.get('active') ==True) & (len(scenario_details.get('triggers'))>0):
            return True
        else:
            return False

    def get_last_runs(self, scenario, days=7):
        """
        Retrieves the last x days of runs of a scenario
        """
        current_datetime = datetime.datetime.now()
        one_week_ago_datetime = current_datetime - datetime.timedelta(days=days)
        runs = scenario.get_runs_by_date(from_date=one_week_ago_datetime, to_date=current_datetime)
        return runs
    

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if any scenarios exceed the maximum number of allowed steps.
        :return: self
        """

        check_pass = True
        message = f"No scenarios are active with triggers and have failed in the last 7 days on the design node"
        result = {}
        
        base_url = self.client.get_general_settings().get_raw().get('studioExternalUrl', "")
        scenarios = self.project.list_scenarios(as_type="objects")
        
        for scenario in scenarios:
            if self.check_for_active_scenario_triggers(scenario):
                runs = self.get_last_runs(scenario, days=7)
                for run in runs:
                    if run.outcome == "FAILED":
                        check_pass = False
                        result[run.id] = base_url +f'/projects/{self.project.project_key}/scenarios/{scenario.id}/runs/list/{run.id}'
                        
        if not check_pass:
            message = f"{len(result)} scenarios are active with triggers on the design node and have failed in the last 7 days"
            
        
        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
