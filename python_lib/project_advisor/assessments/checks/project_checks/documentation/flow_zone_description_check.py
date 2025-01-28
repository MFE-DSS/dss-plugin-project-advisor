import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck




class FlowZoneDescriptionCheck(ProjectCheck):
    """
    A class used to check if a project has for every flow zone at least a short description.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics = List[DSSMetric]
    ):
        """
        Initializes the FlowZoneDescriptionCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="flow_zone_description_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if flow zones have at least a short description.
        :return: self
        """


        flow = self.project.get_flow()
        zones = flow.list_zones()
        check_pass = True
        message = f"All Flow Zones have at least a short description"
        result = {}
        nodesc_zones=[]
        for zone in zones:
            description=zone.get_settings().get_raw()
            if "description" in description and len(description["description"])>0:
                long_desc=description["description"]
            else:
                if "shortDesc" in description and len(description["shortDesc"])>0:
                    short_desc=description["shortDesc"]
                else:
                    check_pass = False
                    nodesc_zones.append(zone.name)
        if nodesc_zones:
            message = f"{nodesc_zones} flow zone(s) identified without a description."
        result["pass"] = check_pass
        result["message"] = message
        #logging.info(f"FlowZoneDescriptionCheck run result : {result}")


        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self