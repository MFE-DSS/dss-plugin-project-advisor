import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class RecipesToMergeCheck(ProjectCheck):
    """
    A class used to check if certain consecutive recipes in the project can be merged into one.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics=List[DSSMetric],
    ):
        """
        Initializes the RecipesToMergeCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.FLOW,
            name="recipes_to_merge_check",
            metrics=metrics,
            description="Checks if certain consecutive recipes in the project can be merged into one.",
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to identify potential recipe merges and replacements.
        :return: self
        """
        all_datasets = self.project.list_datasets(as_type="objects")
        mergeable_recipes = []

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

                if (
                    parent_recipe_type in ["sampling", "distinct"]
                    and child_recipe_type in ["join", "grouping", "window"]
                ) or (
                    parent_recipe_type in ["join", "grouping", "window"]
                    and child_recipe_type in ["sampling", "distinct"]
                ):

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
                        mergeable_recipes.append(
                            {
                                "dataset": dataset.name,
                                "parent_recipe": parent_recipe_id,
                                "child_recipe": child_recipe_id,
                                "engine": parent_recipe_engine,
                            }
                        )
        check_pass = True
        message = ""

        if mergeable_recipes:
            check_pass = False
            message += "Identified datasets where the input and output recipes could be combined:\n"
            for issue in mergeable_recipes:
                message += f"Dataset '{issue['dataset']}' between recipe '{issue['parent_recipe']}' and '{issue['child_recipe']}' using engine '{issue['engine']}' could be optimized.\n"
        else:
            message = "No mergeable recipes were found."

        result = {"mergeable_recipes": mergeable_recipes}
        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
