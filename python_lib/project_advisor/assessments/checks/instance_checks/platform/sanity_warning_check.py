import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class InstanceWarningCheck(InstanceCheck):
    """
    Check that the number of steps in a scenario is below a certain threshold.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the InstanceError instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            batch_project_advisor = batch_project_advisor,
            metrics = metrics,
            category=InstanceCheckCategory.PLATFORM,
            name="instance_warning_check",
            description="Checks the warnings on the DSS sanity report",
        )

    def check_warning_rate_above_zero(self, metric) -> List:
        return metric.value > 0
        
    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if there are any instance warnings from the instance sanity check.
        :return: self
        """

        check_pass = True
        message = "There are no warnings on the instance sanity check report"
        
        warning_messages = []

        
        for metric in self.metrics:
            if (metric.name == "nbr_sanity_check_warnings") & (self.check_warning_rate_above_zero(metric)):
                check_pass = False
                for message in metric.run_result:
                    if message['severity'] == 'WARNING':
                        message = f"There are {metric.value} warnings on the instance sanity check report"
                        warning_messages.append(message)
                
        self.check_pass = check_pass
        self.message = message
        self.run_result = {"warning_messages" :warning_messages}
        return self