import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class FlowZoneSizeCheck(ProjectCheck):
    """
    A class used to check if every flow zone in a project has less than a specified number of datasets.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the FlowZoneSizeCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.FLOW,
            name="flow_zone_size_check",
            metrics=metrics,
            description="Checks if every flow zone in a project has less than a specified number of datasets"
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if flow zones have less than the specified number of datasets.
        :return: self
        """
        config = self.config.get_config()["check_configs"]
        max_datasets_per_flow_zone = config["max_datasets_per_flow_zone"]
        flow = self.project.get_flow()
        zones = flow.list_zones()

        check_pass = True
        message = f"All Flow Zones (or whole project) is under the max number of datasets : {max_datasets_per_flow_zone}"
        result = {}

        if len(zones) == 0:
            nodes = flow.get_graph().nodes
            count = super().count_datasets_in_graph(flow.get_graph())
            if count > max_datasets_per_flow_zone:
                check_pass = False
                message = f"This Flow with no Flow Zones has {count} datasets which is more than the max of {max_datasets_per_flow_zone} datasets."

        else:
            big_zones = []
            for zone in flow.list_zones():
                count = super().count_datasets_in_graph(zone.get_graph())
                if count > max_datasets_per_flow_zone:
                    big_zones.append(zone.name)
                    check_pass = False
            if not check_pass:
                message = f"{len(big_zones)} flow zone(s) identified with more than {max_datasets_per_flow_zone} datasets. See : {big_zones}."
                result["big_zones"] = big_zones

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self