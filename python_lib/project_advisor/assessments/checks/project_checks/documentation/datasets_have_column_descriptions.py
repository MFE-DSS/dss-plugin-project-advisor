import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class DatasetsHaveColumnDescriptions(ProjectCheck):
    """
    A class used to check if source, output, and shared datasets have column descriptions.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics=List[DSSMetric],
    ):
        """
        Initializes the DatasetsHaveColumnDescriptions instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="datasets_have_column_descriptions_check",
            metrics=metrics,
            description="Check if source, output, and shared datasets have column descriptions.",
        )

    def get_published_dataset_ids(self) -> list:
        """
        Retrieves the IDs of published datasets in the project's flow.
        """
        return [d["name"] for d in self.project.list_datasets() if d["featureGroup"]]

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if source, output, and shared datasets have column descriptions.
        :return: self
        """

        check_pass = True
        message = f"All source, output, and shared datasets have column descriptions"
        result = {}

        graph = self.project.get_flow().get_graph()
        source_dataset_ids = [d.id for d in graph.get_source_datasets()]
        output_dataset_ids = super().get_output_dataset_ids(graph)
        published_dataset_ids = self.get_published_dataset_ids()

        no_desc_dataset_ids = []
        to_check_dataset_ids = set(
            source_dataset_ids + output_dataset_ids + published_dataset_ids
        )
        for d_id in to_check_dataset_ids:
            d = self.project.get_dataset(d_id)
            columns = []
            try:
                columns = d.get_schema()["columns"]
            except:
                pass
            for col in columns:
                if "comment" not in col:
                    no_desc_dataset_ids.append(d_id)
                    break

        if no_desc_dataset_ids:
            check_pass = False
            message = f"Found {len(no_desc_dataset_ids)} source, output, or shared datasets without column descriptions. See here: {no_desc_dataset_ids}"

        result["pass"] = check_pass
        result["message"] = message

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
