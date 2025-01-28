import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class InstanceErrorCheck(InstanceCheck):
    """
    Check for errors on the instance sanity report
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the InstanceError instance with the provided client, config.
        """
        super().__init__(
            client=client,
            config=config,
            batch_project_advisor = batch_project_advisor,
            metrics = metrics,
            category=InstanceCheckCategory.PLATFORM,
            name="instance_error_check",
            description="Checks the errors on the DSS sanity report"
        )

    def check_error_rate_above_zero(self, metric) -> List:
        return metric.value > 0
        
    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if there are any instance errors from the instance sanity check.
        :return: self
        """

        check_pass = True
        message = "There are no errors on the instance sanity check report"
        error_messages = []


        for metric in self.metrics:
            if (metric.name == "nbr_sanity_check_errors") & (self.check_error_rate_above_zero(metric)):
                check_pass = False
                for message in metric.run_result:
                    if message['severity'] == 'ERROR':
                        message = f"There are {metric.value} errors on the instance sanity check report"
                        error_messages.append(message)
                
        self.check_pass = check_pass
        self.message = message
        self.run_result = {"error_messages" :error_messages}
        return self


