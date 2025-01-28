import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck




class ProjectWikiHasReferencesCheck(ProjectCheck):
    """
    A class used to check if the project's wiki has references to certain DSS objects.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics: List[DSSMetric]
    ):
        """
        Initializes the ProjectWikiHasReferencesCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="project_wiki_has_references_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project's wiki has references to certain DSS objects.
        :return: self
        """
        check_pass = True
        message = "This Project's wiki has references to all important DSS objects."
        result = {}

        graph = self.project.get_flow().get_graph()
        dss_objects_to_check = []

        for s in self.project.list_scenarios():
            dss_objects_to_check.append(
                {"id": s["id"], "name": s["name"], "type": "scenario"}
            )

        for m in self.project.list_saved_models():
            dss_objects_to_check.append(
                {"id": m["id"], "name": m["name"], "type": "saved_model"}
            )

        for w in self.project.list_webapps():
            dss_objects_to_check.append(
                {"id": w["id"], "name": w["name"], "type": "web_app"}
            )

        for d in self.project.list_dashboards():
            dss_objects_to_check.append(
                {"id": d["id"], "name": d["name"], "type": "dashboard"}
            )

        for f in self.project.get_flow().list_zones():
            dss_objects_to_check.append(
                {"id": f.id, "name": f.name, "type": "flow_zone"}
            )

        for sd in self.project.get_flow().get_graph().get_source_datasets():
            dss_objects_to_check.append(
                {"id": sd.id, "name": sd.name, "type": "source_dataset"}
            )

        for pd in self.project.list_datasets(as_type="object"):
            if pd.get_settings().is_feature_group:
                dss_objects_to_check.append(
                    {"id": pd.id, "name": pd.name, "type": "published_dataset"}
                )

        for od_id in super().get_output_dataset_ids(graph):
            dss_objects_to_check.append(
                {
                    "id": od_id,
                    "name": self.project.get_dataset(od_id).name,
                    "type": "output_dataset",
                }
            )

        dss_objects_not_referenced = []
        concatenated_wiki = " ".join(
            [a.get_data().get_body() for a in self.project.get_wiki().list_articles()]
        )
        for o in dss_objects_to_check:
            if (o["id"] not in concatenated_wiki) and (
                o["name"] not in concatenated_wiki
            ):
                dss_objects_not_referenced.append(o)

        if len(dss_objects_not_referenced) != 0:
            check_pass = False
            result["dss_objects_not_referenced"] = dss_objects_not_referenced
            message = f"This Project's wiki is missing {len(dss_objects_not_referenced)} reference(s) to important objects in your project. See : {dss_objects_not_referenced}."

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self