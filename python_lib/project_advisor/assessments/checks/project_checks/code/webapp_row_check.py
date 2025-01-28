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


class WebappRowCheck(ProjectCheck):
    """
    A class used to check if webapps in a project are under a certain number of rows.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the WebappRowCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.CODE,
            name="webapp_row_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if webapps in a project are under a certain number of rows
        :return: self
        """
        config = self.config.get_config()["check_configs"]
        self.config.get_config()["llm_id"]
        max_nbr_row_webapp = config["max_nbr_row_python_webapp"]

        check_pass = True
        message = f"All Webapps (python code) in the Project are under {max_nbr_row_webapp} lines of code."
        result = {}

        webapps = []
        for webapp in self.project.list_webapps():
            print(webapp["type"])
            if webapp["type"] in ['DASH', 'STANDARD', 'BOKEH']:
                webapps.append(webapp)


        big_python_webapps = []
        for webapp in webapps:
            webapp_name = webapp["name"]
            webapp_current = self.project.get_webapp(webapp["id"])
            settings = webapp_current.get_settings().get_raw()
            python_code = settings["params"]["python"]
            print(python_code)
            if python_code == None:
                python_code = ""
            lines = python_code.split("\n")
            lines = [line for line in lines if line != ""]
            lines = [line for line in lines if not line.startswith("#")]
            lines = [line for line in lines if not line.startswith("import")]
            lines = [line for line in lines if not line.startswith("from")]
            #recipe_py_lines = len(lines)
            if len(lines) > max_nbr_row_webapp:
                big_python_webapps.append(webapp_name)

        if len(big_python_webapps) > 0:
            message = f"{len(big_python_webapps)} webapp(s) has/have been found with more than {max_nbr_row_webapp} lines of python code. See {big_python_webapps}"
            check_pass = False
            result["big_python_webapps"] = big_python_webapps

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
    
    
