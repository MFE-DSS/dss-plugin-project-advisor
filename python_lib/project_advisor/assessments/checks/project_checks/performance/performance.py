import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class UseSQLPushDownCheck(ProjectCheck):
    """
    A class used to check if all recipes in the project leverage SQL push-down computation if applicable.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the UseSQLPushDownCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.PERFORMANCE,
            name="use_sql_push_down_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to identify recipes that could leverage SQL push-down computation.
        :return: self
        """
        check_pass = True
        message = "All recipes leverage SQL push-down computation if applicable."
        result = {}

        recipe_types_to_check = [
            "shaker",
            "sampling",
            "grouping",
            "window",
            "join",
            "distinct",
            "split",
            "topn",
            "sort",
            "pivot",
            "vstack",
        ]
        recipe_items = [
            r for r in self.project.list_recipes() if r.type in recipe_types_to_check
        ]
        flagged_recipes = []

        for r in recipe_items:
            r = r.to_recipe()
            recipe_status = r.get_status()
            try:
                selected_engine_type = recipe_status.get_selected_engine_details()[
                    "type"
                ]
            except:
                selected_engine_type = "not_selected"
            all_selectable_engine_types = [
                e["type"]
                for e in recipe_status.get_engines_details()
                if e["isSelectable"] and e["statusWarnLevel"] == "OK"
            ]

            if "SQL" in all_selectable_engine_types and "SQL" != selected_engine_type:
                flagged_recipes.append(
                    {
                        "name": r.name,
                        "type": r.get_settings().type,
                        "engine": selected_engine_type,
                    }
                )

        if len(flagged_recipes) != 0:
            check_pass = False
            result["flagged_recipes"] = flagged_recipes
            message = f"\nIdentified {len(flagged_recipes)} recipe that could leverage SQL push-down computation."
            for r in flagged_recipes:
                message += f"""
                Recipe {r["name"]} of type {r["type"]},
                is using the execution engine {r["engine"]}, 
                when it could be leveraging SQL push-down computation.
                """

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self


class SQLQueryDatasetCheck(ProjectCheck):
    """
    A class used to check if any dataset in the project is in sql query mode.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the SQLQueryDatasetCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.PERFORMANCE,
            name="sql_query_dataset_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to identify datasets that are in sql query mode.
        :return : self
        """
        check_pass = True
        message = "All SQL datasets are in 'read a database table' mode."
        result = {}

        sql_query_dataset_names = []
        for d in self.project.list_datasets():
            if "params" in d and "mode" in d["params"] and d["params"]["mode"] == "query":
                check_pass = False
                sql_query_dataset_names.append(d["name"])

        if not check_pass:
            result["sql_query_dataset_names"] = sql_query_dataset_names
            message = f"Identified {len(sql_query_dataset_names)} datasets that are in 'SQL query' mode."

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
