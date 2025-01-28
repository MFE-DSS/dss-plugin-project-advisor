import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


from dataikuapi.dss.flow import DSSProjectFlowGraph


class DatasetDataQualityRulesCheck(ProjectCheck):
    """
    A class used to check if datasets in the project have associated data quality rules and if those rules are validated in scenarios.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics: List[DSSMetric],
    ):
        """
        Initializes the DatasetDataQualityRulesCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.ROBUSTNESS,
            name="dataset_data_quality_rules_check",
            metrics=metrics,
            dss_version_min=Version("12.6.0"),
        )

    def get_dataset_ids_in_scenarios_with_check_step(self) -> list:
        """
        Retrieves the IDs of datasets validated in scenarios with check steps.

        :return: A list of dataset IDs.
        :rtype: list
        """
        scenarios = self.project.list_scenarios(as_type="objects")
        dataset_ids = []

        for s in scenarios:
            scenario_settings = s.get_settings().get_raw()
            if scenario_settings["type"] == "step_based":
                for step in scenario_settings["params"]["steps"]:
                    if step["type"] == "check_dataset":
                        for check in step["params"]["checks"]:
                            dataset_ids.append(check["itemId"])

        return list(set(dataset_ids))

    def run(self) -> ProjectCheck:
        """
        Runs the check to ensure datasets have associated data quality rules and are validated in scenarios.
        :return : self
        """
        graph = self.project.get_flow().get_graph()
        source_dataset_ids = [d.id for d in graph.get_source_datasets()]
        output_dataset_ids = super().get_output_dataset_ids(graph)
        published_dataset_ids = [
            d["name"] for d in self.project.list_datasets() if d["featureGroup"]
        ]
        validated_dataset_ids = self.get_dataset_ids_in_scenarios_with_check_step()
        dataset_ids_with_rules = [
            d["name"]
            for d in self.project.list_datasets()
            if len(d["metricsChecks"]["checks"]) != 0
        ]

        check_pass = True
        message = ""
        result = {}

        source_dataset_ids_without_rules = [
            d for d in source_dataset_ids if d not in dataset_ids_with_rules
        ]
        source_dataset_ids_with_rules = [
            d for d in source_dataset_ids if d in dataset_ids_with_rules
        ]
        source_dataset_ids_without_scenarios = [
            d for d in source_dataset_ids_with_rules if d not in validated_dataset_ids
        ]
        source_dataset_ids_with_scenarios = [
            d for d in source_dataset_ids_with_rules if d in validated_dataset_ids
        ]

        output_dataset_ids_without_rules = [
            d for d in output_dataset_ids if d not in dataset_ids_with_rules
        ]
        output_dataset_ids_with_rules = [
            d for d in output_dataset_ids if d in dataset_ids_with_rules
        ]
        output_dataset_ids_without_scenarios = [
            d for d in output_dataset_ids_with_rules if d not in validated_dataset_ids
        ]
        output_dataset_ids_with_scenarios = [
            d for d in output_dataset_ids_with_rules if d in validated_dataset_ids
        ]

        published_dataset_ids_without_rules = [
            d for d in published_dataset_ids if d not in dataset_ids_with_rules
        ]
        published_dataset_ids_with_rules = [
            d for d in published_dataset_ids if d in dataset_ids_with_rules
        ]
        published_dataset_ids_without_scenarios = [
            d
            for d in published_dataset_ids_with_rules
            if d not in validated_dataset_ids
        ]
        published_dataset_ids_with_scenarios = [
            d for d in published_dataset_ids_with_rules if d in validated_dataset_ids
        ]

        if not (
            len(source_dataset_ids)
            == len(source_dataset_ids_with_rules)
            == len(source_dataset_ids_with_scenarios)
        ):
            check_pass = False
            message = f"""
                        Identified {len(source_dataset_ids_without_rules)} source dataset(s) without any Data Quality Rules : See {source_dataset_ids_without_rules}.
                        Additionally, found {len(source_dataset_ids_without_scenarios)} source dataset(s) with Rules that are not validated in a Scenario. See {source_dataset_ids_without_scenarios}
                        """
            result["source_dataset_ids_without_rules"] = (
                source_dataset_ids_without_rules
            )
            result["source_dataset_ids_without_scenarios"] = (
                source_dataset_ids_without_scenarios
            )

        if not (
            len(output_dataset_ids)
            == len(output_dataset_ids_with_rules)
            == len(output_dataset_ids_with_scenarios)
        ):
            check_pass = False
            message += f"""
                        Identified {len(output_dataset_ids_without_rules)} output dataset(s) without any Data Quality Rules. See {output_dataset_ids_without_rules}.
                        Additionally, found {len(output_dataset_ids_without_scenarios)} output dataset(s) with Rules that are not validated in a Scenario. See {output_dataset_ids_without_scenarios}.
                        """
            result["output_dataset_ids_without_rules"] = (
                output_dataset_ids_without_rules
            )
            result["output_dataset_ids_without_scenarios"] = (
                output_dataset_ids_without_scenarios
            )

        if not (
            len(published_dataset_ids)
            == len(published_dataset_ids_with_rules)
            == len(published_dataset_ids_with_scenarios)
        ):
            check_pass = False
            message += f"""
                        Identified {len(published_dataset_ids_without_rules)} published dataset(s) without any Data Quality Rules. See {published_dataset_ids_without_rules}.
                        Additionally, found {len(published_dataset_ids_without_scenarios)} published dataset(s) with Rules that are not validated in a Scenario. See {published_dataset_ids_without_scenarios}
                        """
            result["published_dataset_ids_without_rules"] = (
                published_dataset_ids_without_rules
            )
            result["published_dataset_ids_without_scenarios"] = (
                published_dataset_ids_without_scenarios
            )

        if check_pass:
            message = "All source, output, and published datasets have data quality rules that are also validated in a scenario"

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
