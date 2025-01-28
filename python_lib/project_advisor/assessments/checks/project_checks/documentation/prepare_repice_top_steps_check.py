import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class PrepareRecipesTopLevelSteps(ProjectCheck):
    """
    A class used to check if prepare recipes have no more than X top level steps, with X being configurable in the project config preset
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics=List[DSSMetric],
    ):
        """
        Initializes the PrepareRecipesTopLevelSteps instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="prepare_recipes_top_level_steps_check",
            metrics=metrics,
            description="Check if prepare recipes have no more than X top level steps, with X being configurable in the project config preset",
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if prepare recipes have no more than X top level steps.
        :return: self
        """
        
        check_pass = True
        max_nbr_top_level_steps_prepare_recipe = self.config.get_config()["check_configs"]["max_nbr_top_level_steps_prepare_recipe"]
        message = f"All prepare recipes have less than {max_nbr_top_level_steps_prepare_recipe} top level steps"
        result = {}
        
        # Get a list of all prepare recipes in the project
        prepare_recipes = [recipe.name for recipe in self.project.list_recipes() if recipe.type == 'shaker']

        offending_prepare_recipes = []
        
        for recipe_name in prepare_recipes:
            prep_recipe_settings = self.project.get_recipe(recipe_name).get_settings()
            top_level_steps = [ step for step in prep_recipe_settings.raw_steps if step['metaType'] != 'GROUP' ]
            if len(top_level_steps) > max_nbr_top_level_steps_prepare_recipe:
                offending_prepare_recipes.append(recipe_name)


        if offending_prepare_recipes:
            check_pass = False
            message = f"Found {len(offending_prepare_recipes)} prepare recipes with more than {max_nbr_top_level_steps_prepare_recipe} top level steps. See here: {offending_prepare_recipes}"

        result["pass"] = check_pass
        result["message"] = message

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self