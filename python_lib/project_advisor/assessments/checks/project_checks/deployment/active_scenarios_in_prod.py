import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ProjectHasProdActiveScenario(ProjectCheck):
    """
    A class used to check if a project has at least one scneario with auto-triggers in each of its deployments.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectHasProdActiveScenario instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DEPLOYMENT,
            name="check_project_has_active_scenario_in_prod",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project has at least one scneario with auto-triggers in each of its deployments.
        :return: self
        """
        
        project_key = self.project.project_key
        self.config.logger.debug(f"Running check_project_has_active_scenario_in_prod in {project_key}")
        
        check_pass = True
        message = f"Project {project_key} has at least an auto-triggered scenario in all deployments."
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
            
            # Compute a mapping between the design project key and the deployment project key
            if self.config.deployment_project_mapping is None:
                deployment_project_mapping = dict()
                deployments = project_deployer.list_deployments()
                for deployment in deployments:
                    deployments_info = deployment.get_status().get_light()
                    design_project_key = deployments_info["packages"][-1]["designNodeInfo"]["projectKey"]
                    deployed_project_key = deployments_info["deploymentBasicInfo"]["deployedProjectKey"]
                    deployment_project_mapping.setdefault(design_project_key, list()).append(deployed_project_key)
            else:
                # Retrieve a pre-computed mapping between the design project key and the deployment project key
                deployment_project_mapping = self.config.deployment_project_mapping
                    
            if project_key not in deployment_project_mapping:
                message = f"Project {project_key} has no deployment in production." 
            else:
                infra_no_active_projects = dict()
                # Check if the deployements has at least one auto-triggered scenario in each infrastructure where the project has been deployed
                for infra_id, infra_client in self.config.infra_to_client.items():
                    deployed_project_keys = deployment_project_mapping[project_key]
                    infra_project_keys = infra_client.list_project_keys()
                    for deployed_project_key in deployed_project_keys:
                        if deployed_project_key in infra_project_keys:
                            deployed_project =  infra_client.get_project(deployed_project_key)
                            scenarios = deployed_project.list_scenarios(as_type="objects")
                            active_scenarios = [(scenario.get_settings().get_raw().get('active')==True) 
                                                & (len(scenario.get_settings().get_raw().get('triggers'))>0) 
                                                for scenario in scenarios]
                            if not any(active_scenarios):
                                infra_no_active_projects.setdefault(infra_id, list()).append(deployed_project_key)

                if any(len(infra_no_active_project) != 0 for infra_id, infra_no_active_project in infra_no_active_projects.items()):
                    check_pass = False
                    message = "Project does not have at least an auto-triggered scenario in all infrastructures"           
                    run_result["deployed_project_without_active_scenario_by_infra"] = infra_no_active_projects

        self.check_pass = check_pass
        self.message = message
        self.run_result = run_result
        return self
    
    
    
    