import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class ConsecutivePrepareRecipesCheck(ProjectCheck):
    """
    A class used to check that no two prepare recipes follow each other in the flow,
    unless they use different computation engines.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics: List[DSSMetric],
    ):
        """
        Initializes the ConsecutivePrepareRecipesCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.FLOW,
            name="consecutive_prepare_recipe_check",
            metrics=metrics,
            description="Checks that no two prepare recipes follow each other in the flow, unless they use different computation engines",
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if there are any consecutive prepare recipes using the same computation engine.
        :return: self
        """

        all_datasets = self.project.list_datasets(as_type="objects")
        consecutive_prepare_issues = []

        for dataset in all_datasets:

            child_recipes = dataset.get_info().get_raw()["recipes"]
            parent_recipes = []
            try:
                parent_recipes.append(dataset.get_info().get_raw()["creatingRecipe"])
            except KeyError:
                pass

            if len(parent_recipes) == 1 and len(child_recipes) == 1:
                parent_recipe_id = parent_recipes[0]["id"]
                parent_recipe_type = parent_recipes[0]["type"]
                child_recipe_id = child_recipes[0]["id"]
                child_recipe_type = child_recipes[0]["type"]

                if parent_recipe_type == "shaker" and child_recipe_type == "shaker":
                    parent_recipe_engine = (
                        self.project.get_recipe(parent_recipe_id)
                        .get_status()
                        .get_selected_engine_details()["type"]
                    )
                    child_recipe_engine = (
                        self.project.get_recipe(child_recipe_id)
                        .get_status()
                        .get_selected_engine_details()["type"]
                    )

                    if parent_recipe_engine == child_recipe_engine:
                        consecutive_prepare_issues.append(
                            {
                                "dataset": dataset.name,
                                "parent_recipe": parent_recipe_id,
                                "child_recipe": child_recipe_id,
                                "engine": parent_recipe_engine,
                            }
                        )

        check_pass = True
        message = ""

        if consecutive_prepare_issues:
            check_pass = False
            message += "Identified datasets where the input and output prepare recipes use the same computation engine, suggesting they could be combined:\n"
            for issue in consecutive_prepare_issues:
                message += f"Dataset '{issue['dataset']}' between prepare recipes '{issue['parent_recipe']}' and '{issue['child_recipe']}' using engine '{issue['engine']}' could be optimized.\n"
        else:
            message = "No consecutive prepare recipes with the same computation engine were found."

        result = {"consecutive_prepare_issues": consecutive_prepare_issues}

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
