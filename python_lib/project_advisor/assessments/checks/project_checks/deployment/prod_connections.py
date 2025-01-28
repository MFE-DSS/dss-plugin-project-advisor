import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ProjectHasConnectionsInProd(ProjectCheck):
    """
    A class used to check if a project has all its connections in the production infrastructure.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectHasConnectionsInProd instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DEPLOYMENT,
            name="check_project_connections_in_production",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project has all its connections in the automation infrastructures.
        :return: self
        """
        
        project_key = self.project.project_key
        self.config.logger.debug(f"Running check_project_connections_in_production in {project_key}")
        
        check_pass = True
        message = f"Project {project_key} has all its connections already created in the production infrastructure(s)."
        run_result = {}

        # Check if the deployer client has been successful loaded, if not, notify that the check is not possible
        if self.config.deployer_client == None:
            check_pass = None
            message = "Deployment best practices can't be checked with the current deployer configuration" 
        # Check if the infrastruture clients has been successful loaded, if not, notify that the check is not possible
        elif any(infra_client is None for infra_id, infra_client in self.config.infra_to_client.items()):
            check_pass = None
            message = "Deployment best practices can't be checked with the current deployment infrastruture configuration" 
        else:
            project_deployer = self.config.deployer_client.get_projectdeployer()
            
            # Compute the plugins usage across the instance
            data_object_descs = self.project.list_datasets() + self.project.list_managed_folders()
            connections = set()
            for data_object_desc in data_object_descs:
                if "connection" in data_object_desc["params"]:
                    connections.add(data_object_desc["params"]["connection"])
                    
            # Retrieve the existing connection remappings from the deployments        
            connection_remappings = dict()
            for deployment in project_deployer.list_deployments():
                deployment_remappings = deployment.get_settings().get_raw()["bundleContainerSettings"]["remapping"]["connections"]
                for deployment_remapping in deployment_remappings:
                    connection_remappings[deployment_remapping["source"]] = deployment_remapping["target"]

            infra_missing_connections = dict()
            infra_project_remappings = dict()
            
            # Compute the missing connections per infrastructure
            for infra_id, infra_client in self.config.infra_to_client.items():
                # List the connections in the infra
                infra_connections = set(infra_client.list_connections().keys())
                # List the remappings in the deployer with a valid target in the infra
                valid_remappings = {source: target for source, target in connection_remappings.items() if target in infra_connections}
                # Compute the missing connections according to the infra
                missing_connections = connections - infra_connections
                # Take into account the valid remappings
                missing_connections_after_remapping = missing_connections - set(valid_remappings.keys())
                infra_missing_connections[infra_id] = list(missing_connections_after_remapping)
                # Compute the remappings relevant to the project
                valid_project_remmapings = missing_connections.intersection(set(valid_remappings.keys()))
                infra_project_remappings[infra_id] = {source: target for source, target in valid_remappings.items() if source in valid_project_remmapings}

            if any(len(infra_missing_connection) != 0 for infra_id, infra_missing_connection in infra_missing_connections.items()):
                check_pass = False
                message = f"Connections are missing in production infrastructures for project {project_key}."  
                run_result["missing_connections_by_infra"] = infra_missing_connections
                
            if any(len(infra_project_remapping) != 0 for infra_id, infra_project_remapping in infra_project_remappings.items()):
                run_result["valid_project_remappings_by_infra"] = infra_project_remappings
                
        self.check_pass = check_pass
        self.message = message
        self.run_result = run_result
        return self
    
    
    
    