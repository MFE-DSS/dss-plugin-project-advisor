import dataikuapi
from typing import List
from packaging.version import Version

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

class SQLRecipeToVisualCheck(ProjectCheck):

    """
    A class used to check if a SQL recipe can be converted to a visual recipe in Dataiku DSS.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric],
    ):
        """
        Initializes the SQLRecipeToVisualCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.CODE,
            name="sql_to_visual_check",
            metrics = metrics,
            dss_version_min=Version("12.4.0")
        )
        self.has_llm = True
    
    def get_sql_to_visual_chain(self) -> RunnableSequence:
        system_message_prompt = """
        You are a Dataiku DSS expert and a sql expert.
        Your job is to identify if sql code in a sql recipe in Dataiku can be replaced by a visual recipe.
        As a reminder, the visual transformation recipes are:
        Sync : copy data from an input to an output Dataset
        Prepare : Transforms the data row by row
        Sample / Filter : Sample filter rows in a Dataset
        Group :  Aggregate the values of columns by the values of one or more keys.
        Distinct : Allows you to filter a dataset in order to remove some of its duplicate rows.
        Window :  Compute ordered window aggregations of columns by the values of one or more keys.
        Join : enrich one dataset with columns from another.
        Fuzzy join : joining datasets based on similarity matching conditions
        Geo join : joining datasets based on geographic conditions
        Split : Divides a dataset into two or more parts based on a condition
        Top N : Allows you to filter a dataset based on the top and bottom values of some of its rows.
        Sort : Allows you to sort the rows of an input dataset by the values of one or more columns in the dataset.
        Pivot : transforms datasets into pivot tables, which are tables of summary statistics
        Stack : Combines the rows of two or more datasets into a single output dataset
        """

        human_message = """
        Here is the sql code recipe:
        {sql_code}
        Please tell me if this sql code can be replaced by a visual recipe in Dataiku DSS and which one to use. Format the response in a json format with the following keys:
        convertible : Boolean
        explanation : String
        visual_recipe : List[DSS visual recipes]

        If it is not possible reply {{"convertible" : false}}
        """
        llm_id=self.config.get_config()["llm_id"]
        model = self.get_lc_model(llm_id, 0.2)

        messages = [
            SystemMessage(content=system_message_prompt),
            HumanMessagePromptTemplate(
                prompt=PromptTemplate.from_template(human_message)
            ),
        ]
        chat_template = ChatPromptTemplate.from_messages(messages)
        chain = chat_template | model | JsonOutputParser()
        return chain

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if SQL recipes can be converted to visual recipes.
        :return: self
        """
        config = self.config.get_config()
        check_pass = True
        message = f"No SQL Recipes can be converted to visual recipes."
        result = {}

        chain = self.get_sql_to_visual_chain()

        sql_recipes = []
        for recipe in self.project.list_recipes():
            if recipe["type"] == "sql_query":
                sql_recipes.append(recipe)

        convertible_sql_recipes = {}
        try:
            for recipe in sql_recipes:
                recipe_name = recipe["name"]
                recipe = self.project.get_recipe(recipe_name)
                settings = recipe.get_settings()
                sql_code = settings.get_payload()
                if sql_code == None:
                    res = {"convertible" : True, "explanation" : "SQL Recipe has never been edited", "visual_recipe" : ["Sync"]}
                else:
                    res = chain.invoke({"sql_code": sql_code})
                if res["convertible"] == True:
                    convertible_sql_recipes[recipe_name] = res
        except Exception as e:
            result["pass"] = None
            result["message"] = f"LLM error : {str(e)}"
            return result

        if len(convertible_sql_recipes) > 0:
            message = f"{len(convertible_sql_recipes)} SQL recipe(s) have been identified as convertible to visual recipes. See {convertible_sql_recipes.keys()}"
            check_pass = False
            result["recommendations"] = convertible_sql_recipes

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self