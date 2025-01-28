import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class FlowSizeCheck(ProjectCheck):
    """
    A class used to check if a project has less than a specified number of datasets in its flow.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics = List[DSSMetric]
    ):
        """
        Initializes the FlowSizeCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.FLOW,
            name="flow_size_check",
            metrics=metrics,
            description="Checks if a project has less than a specified number of datasets in its flow."
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project flow has less than the specified number of datasets.
        :return: self
        """
        config = self.config.get_config()["check_configs"]
        max_datasets_per_flow = config["max_datasets_per_flow"]
        flow = self.project.get_flow()

        check_pass = True
        message = f"The project's Flow is under the max number of datasets : {max_datasets_per_flow}"
        result = {}

        count = super().count_datasets_in_graph(flow.get_graph())
        if count > max_datasets_per_flow:
            check_pass = False
            message = f"This Flow has {count} datasets which is more than the max of {max_datasets_per_flow} datasets."

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self