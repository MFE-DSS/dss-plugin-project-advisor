import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class NoUnusedDatasetCheck(ProjectCheck):
    """
    A class used to check if all datasets in the project are either explicitly built or are part of the dependencies of a build job in a scenario.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics: List[DSSMetric]
    ):
        """
        Initializes the NoUnusedDatasetCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.ROBUSTNESS,
            name="no_unused_dataset_check",
            metrics=metrics,
            description="Check if all datasets in the project are either explicitly built or are part of the dependencies of a build job in a scenario.",
        )

    def find_connected_datasets(
        self, nodes: dict, node_id: str, direction: str = "upstream"
    ) -> list:
        """
        Find all datasets connected to a given node in a specified direction.

        This function uses Depth-First Search (DFS) to traverse the graph and find all datasets
        that are either upstream or downstream of a specified node.

        :param nodes: List of nodes where each node is a dictionary with 'id', 'predecessors', and 'successors'.
        :type nodes: dict of dicts
        :param node_id: The ID of the node for which to find connected datasets.
        :type node_id: int
        :param direction: The direction of the search. 'upstream' to find predecessors, 'downstream' to find successors. Defaults to 'upstream'.
        :type direction: str

        :return: A list of node IDs that are connected to the specified node in the given direction.
        :rtype: list of str
        """
        visited = set()
        connected_nodes = []

        def dfs(current_id):
            visited.add(current_id)
            current_node = nodes[current_id]

            if direction == "upstream":
                neighbors = current_node["predecessors"]
            else:
                neighbors = current_node["successors"]

            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    dfs(neighbor_id)

            if current_node["type"] == "COMPUTABLE_DATASET":
                connected_nodes.append(current_id)

        dfs(node_id)
        connected_nodes.remove(node_id)

        return connected_nodes

    def get_dataset_ids_in_scenarios_with_build_step(self) -> list:
        """
        Retrieves the IDs of datasets built in scenarios with a build step.

        :return: A list of dataset IDs.
        :rtype: list
        """
        scenarios = self.project.list_scenarios(as_type="objects")
        dataset_ids = []

        for s in scenarios:
            scenario_settings = s.get_settings().get_raw()
            if scenario_settings["type"] == "step_based":
                for step in scenario_settings["params"]["steps"]:
                    if step["type"] == "build_flowitem":
                        for build in step["params"]["builds"]:
                            if build["type"] == "DATASET":
                                dataset_ids.append(
                                    {
                                        "id": build["itemId"],
                                        "jobType": step["params"]["jobType"],
                                    }
                                )

        return dataset_ids

    def run(self) -> ProjectCheck:
        """
        Runs the check to ensure all datasets are either explicitly built or are part of the dependencies of a build job in a scenario.

        :return: self
        """
        check_pass = True
        message = "All datasets in this project are either explicitly built or are part of the dependencies of a build job in a scenario."
        result = {}

        nodes = self.project.get_flow().get_graph().nodes
        datasets_to_check = self.get_dataset_ids_in_scenarios_with_build_step()
        datasets_used = [d["id"] for d in datasets_to_check]
        datasets_all = [
            d_id for d_id in nodes if nodes[d_id]["type"] == "COMPUTABLE_DATASET"
        ]

        for d in datasets_to_check:
            if (
                d["jobType"] == "RECURSIVE_BUILD"
                or d["jobType"] == "RECURSIVE_FORCED_BUILD"
            ):
                datasets_upstream = self.find_connected_datasets(nodes, d["id"])
                datasets_used += datasets_upstream
            elif d["jobType"] == "RECURSIVE_BUILD":
                datasets_downstream = self.find_connected_datasets(
                    nodes, d["id"], direction="downstream"
                )
                datasets_used += datasets_downstream

        datasets_unused = list(set(datasets_all) - set(datasets_used))
        if len(datasets_unused) != 0:
            check_pass = False
            result["datasets_unused"] = datasets_unused
            message = f"{len(datasets_unused)} datasets in this project are not covered by a scenario. See here: {datasets_unused}"

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self
