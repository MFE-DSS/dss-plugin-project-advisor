import dataikuapi
from typing import List
from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ScenarioTimeTriggerPeriodCheck(ProjectCheck):
    """
    Checks that all time-based scenario triggers have a period greater than 5 minutes.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics: List[DSSMetric]
    ):
        """
        Initializes the ScenarioTimeTriggerPeriodCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.AUTOMATION,
            name="scenario_time_trigger_period_check",
            metrics=metrics
        )
        
    def calculate_trigger_period_in_minutes(self, frequency, repeat_frequency):
        """
        Calculates the period in minutes based on the frequency and repeatFrequency values.
        """
        
        if frequency == 'Minutely':
            return repeat_frequency
        elif frequency == 'Hourly':
            return repeat_frequency * 60
        elif frequency == 'Daily':
            return repeat_frequency * 24 * 60
        elif frequency == 'Weekly':
            return repeat_frequency * 7 * 24 * 60
        elif frequency == 'Monthly':
            # Assuming 30 days in a month for simplicity
            return repeat_frequency * 30 * 24 * 60
        else:
            # Handle unknown or unsupported frequencies
            return float('inf')

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if all time-based scenario triggers have a period greater than 5 minutes.
        :return: self
        """
        config = self.config.get_config()["check_configs"]
        min_scenario_trigger_time_period = config["min_scenario_trigger_time_period"]
        
        check_pass = True
        message = "All time-based scenario triggers have a period greater than 5 minutes."
        result = {}

        scenarios = self.project.list_scenarios(as_type="objects")
        for scenario in scenarios:
            scenario_settings = scenario.get_settings().get_raw()
            for trigger in scenario_settings.get('triggers', []):
                if trigger['type'] == 'temporal':  # Checking for time-based triggers
                    frequency = trigger['params'].get('frequency')
                    repeat_frequency = trigger['params'].get('repeatFrequency', 1)
                    
                    # Convert the frequency to minutes
                    period_in_minutes = self.calculate_trigger_period_in_minutes(frequency, repeat_frequency)
                    
                    if period_in_minutes <= min_scenario_trigger_time_period:
                        check_pass = False
                        result[scenario.id] = {
                            "scenario_name": scenario.get_definition().get('name'),
                            "period_in_minutes": period_in_minutes
                        }

        if not check_pass:
            message = f"{len(result)} scenario(s) have a time trigger period of 5 minutes or less."

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self