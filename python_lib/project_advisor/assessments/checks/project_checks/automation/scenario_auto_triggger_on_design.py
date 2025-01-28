import dataikuapi
from typing import List
import datetime
from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ScenarioWithAutoTriggerOnDesignNodeCheck(ProjectCheck):
    """
    Checks if any active scenarios have a trigger set up on the design node
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ScenarioWithAutoTriggerOnDesignCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.AUTOMATION,
            name="scenario_with_autotrigger_on_design_node_check",
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


    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if any scenarios have an
        :return: self
        """

        check_pass = True
        message = f"No scenarios are active with automatics triggers on the design node"
        result = []
        

        scenarios = self.project.list_scenarios(as_type="objects")
        
        for scenario in scenarios:
            if self.check_for_active_scenario_triggers(scenario):
                check_pass = False
                result.append(scenario.id)
                
        if not check_pass:
            message = f"{len(result)} scenarios are active with triggers on the design node"
            
        
        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self