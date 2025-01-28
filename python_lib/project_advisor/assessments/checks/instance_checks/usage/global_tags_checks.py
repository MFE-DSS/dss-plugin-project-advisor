import dataikuapi
import pandas as pd
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor


class GlobalTagsCheck(InstanceCheck):
    """
    A class that checks if global tags are defined are defined for all required objects (i.e. projects, datasets, recipes, scenarios, and dashboards).
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the GlobalTagsCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics = metrics,
            batch_project_advisor = batch_project_advisor,
            category=InstanceCheckCategory.USAGE,
            name="global_tags_check",
            description="Checks if global tags are defined are defined for all required objects (i.e. projects, datasets, recipes, scenarios, and dashboards)."
        )

    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if global tags are defined are defined for all required objects (i.e. projects, datasets, recipes, scenarios, and dashboards).
        :return: self
        """

        settings = self.client.get_general_settings()
        raw_settings = settings.get_raw().get("globalTagsCategories", [])

        required_objects = {'PROJECT', 'DATASET', 'RECIPE', 'SCENARIO', 'DASHBOARD'}

        category_apply = set()
        category_missing_tags = []
        other_missing_tags = []

        if not raw_settings:
            check_pass = False
            message = "No global tags categories have been defined"
        else:
            for category in raw_settings:
                applies_to_set = set(category['appliesTo'])

                if applies_to_set & required_objects:
                    category_apply.update(applies_to_set & required_objects)

                    if not category['globalTags']:
                        category_missing_tags.append(category["name"])
                elif not category['globalTags']:
                    other_missing_tags.append(category["name"])

            missing_objects = required_objects - category_apply

            if missing_objects or category_missing_tags:
                check_pass = False
                message = (
                    "Global tags categories are defined but not for all the required objects "
                    "(i.e. projects, datasets, recipes, scenarios, and dashboards), or there are categories without tags."
                )
                result = {
                    "Missing required object categories": {
                        "Covered objects": list(category_apply),
                        "Missing objects": list(missing_objects)
                    },
                    "Categories without tags": category_missing_tags
                }
            else:
                check_pass = True
                message = (
                    "Global tags categories are defined for all the required objects "
                    "(i.e. projects, datasets, recipes, scenarios, and dashboards)."
                )

                if other_missing_tags:
                    message += " However, some other categories are defined without tags."
                    result = {"Other categories without tags": other_missing_tags}


        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self