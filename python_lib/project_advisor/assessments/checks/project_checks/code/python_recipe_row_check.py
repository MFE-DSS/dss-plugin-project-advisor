import dataikuapi
from typing import List

import langchain_core
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables.base import RunnableSequence

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck

from typing import Any, Dict

class PythonRecipeRowCheck(ProjectCheck):
    """
    A class used to check if Python recipes in a project are under a certain number of rows.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the PythonRecipeRowCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.CODE,
            name="python_recipe_row_check",
            metrics = metrics
        )
   

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if Python recipes are under a specified number of rows.
        :return: self
        """
        config = self.config.get_config()["check_configs"]
        max_nbr_row_python_recipe = config["max_nbr_row_python_recipe"]
        check_pass = True
        message = f"All Python Recipes in the Flow are under {max_nbr_row_python_recipe} lines of code."
        result = {}

        python_recipes = []
        for recipe in self.project.list_recipes():
            if recipe["type"] == "python":
                python_recipes.append(recipe)

        big_python_recipes = []
        for recipe in python_recipes:
            recipe_name = recipe["name"]
            recipe = self.project.get_recipe(recipe_name)
            settings = recipe.get_settings()
            python_code = settings.get_code()
            if python_code == None:
                python_code = ""
            lines = python_code.split("\n")
            lines = [line for line in lines if line != ""]
            lines = [line for line in lines if not line.startswith("#")]
            lines = [line for line in lines if not line.startswith("import")]
            lines = [line for line in lines if not line.startswith("from")]
            recipe_py_lines = len(lines)
            if len(lines) > max_nbr_row_python_recipe:
                big_python_recipes.append(recipe_name)

        if len(big_python_recipes) > 0:
            message = f"{len(big_python_recipes)} recipe(s) have been found with more than {max_nbr_row_python_recipe} lines of code. See {big_python_recipes}"
            check_pass = False
            result["big_python_recipes"] = big_python_recipes

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
    
    
