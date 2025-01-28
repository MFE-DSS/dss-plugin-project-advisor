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


class ProjectCodeEnvSetCheck(ProjectCheck):
    """
    A class used to check if a project has a code env set when there is a python recipe present
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the Check instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.CODE,
            name="default_project_code_env_check",
            metrics = metrics
        )
        
    def has_recipe_type(self, recipe_type: str) -> bool:
        """
        Checks if there is any recipe of a given type in the project's list of recipes.

        :param recipe_type: The type of recipe to check for.
        :type recipe_type: str
        :return: True if a recipe of the specified type is found, False otherwise.
        :rtype: bool
        """
        return any(recipe["type"] == recipe_type for recipe in self.project.list_recipes())
    
    def has_scenario_type(self, scenario_type: str) -> bool:
        """
        Checks if there is any scenario of a given type in the project's list of scenarios.

        :param scenario_type: The type of scenario to check for.
        :type scenario_type: str
        :return: True if a scenario of the specified type is found, False otherwise.
        :rtype: bool
        """
        return any(scenario['type'] == scenario_type for scenario in self.project.list_scenarios())

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if project has a code env set when there is a python recipe present.
        :return: self
        """
        # Fetch the settings for Python and R code environments
        code_envs_settings = self.project.get_settings().get_raw().get('settings').get('codeEnvs')
        python_code_env_settings = code_envs_settings.get('python')
        r_code_env_settings = code_envs_settings.get('r')
        
        message = f"There were no code recipes in the project so no all checks passed"
        result = {}

        # Determine if Python or R recipes/scenarios exist
        has_python = self.has_recipe_type("python") or self.has_scenario_type("custom_python")
        has_r = self.has_recipe_type("r")

        # Initialize the check_pass flag
        check_pass = True
        
        if has_python or has_r:
            message = "The project contains: "
            
            # Validate the environment settings for Python
            if has_python and (not python_code_env_settings.get('mode') or python_code_env_settings.get('mode') != "EXPLICIT_ENV"):
                check_pass = False
                message += "Python code in the Scenarios or Recipes and the codeEnv is not set at project level."

            # Validate the environment settings for R
            if has_r and (not r_code_env_settings.get('mode') or r_code_env_settings.get('mode') != "EXPLICIT_ENV"):
                check_pass = False
                message += "R code in the Recipes and the codeEnv is not set at project level."
            else:
                message += "Code in the Recipes or Scenarios with a project codeEnv set"
                
        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self