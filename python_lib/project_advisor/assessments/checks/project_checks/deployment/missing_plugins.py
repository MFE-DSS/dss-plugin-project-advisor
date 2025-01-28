import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ProjectHasPluginsInProd(ProjectCheck):
    """
    A class used to check if a project has all its used plugins in the production infrastructure.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectHasPluginsInProd instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DEPLOYMENT,
            name="check_project_plugins_in_production",
            metrics = metrics
        )
        self.uses_plugin_usage = True

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project has all used plugins in the automation infrastructures.
        :return: self
        """
        
        project_key = self.project.project_key
        self.config.logger.debug(f"Running check_project_plugins_in_production in {project_key}")
        
        check_pass = True
        message = f"Project {project_key} has all plugins already installed in the production infrastructure(s)."
        run_result = {}
        
        deployer_projects_to_publish = list()
        infra_projects_to_deploy = dict()

        # Check if the deployer client has been successful loaded, if not, notify that the check is not possible
        if self.config.deployer_client == None:
            check_pass = None
            message = "Deployment best practices can't be checked with the current deployer configuration" 
        # Check if the infrastruture clients has been successful loaded, if not, notify that the check is not possible
        elif any(infra_client is None for infra_id, infra_client in self.config.infra_to_client.items()):
            check_pass = None
            message = "Deployment best practices can't be checked with the current deployment infrastruture configuration" 
        else: 
            if self.config.plugins_usage is None:
                check_pass = None
                message = "Plugin usage was not computed" 
            else:    
                project_plugin_usage = self.config.plugins_usage
                if project_key not in project_plugin_usage:
                    message = "No plugin used in this project."
                else:
                    # Retrieve projects on the deployer and the infrastructures
                    project_deployer = self.config.deployer_client.get_projectdeployer()
                    deployer_projects = [deployer_project.project_key for deployer_project in project_deployer.list_projects()]
                    infra_projects = {infra_id: infra_client.list_project_keys() for infra_id, infra_client in self.config.infra_to_client.items()}

                    # Retrieve the plugins used in the current project
                    current_project_plugins = project_plugin_usage[project_key]

                    infra_missing_plugins = dict()
                    # Compute the missing plugins in every automation node for the current project
                    for infra_id, infra_client in self.config.infra_to_client.items():
                        infra_plugins = set(plugin["id"] for plugin in infra_client.list_plugins())
                        missing_plugins = current_project_plugins - infra_plugins
                        infra_missing_plugins[infra_id] = list(missing_plugins)

                    if any(len(infra_missing_plugin) != 0 for infra_id, infra_missing_plugin in infra_missing_plugins.items()):
                        check_pass = False
                        message = f"Plugins are not installed in production infrastructures for project {project_key}."  
                        run_result["missing_plugins_by_infra"] = infra_missing_plugins

        self.check_pass = check_pass
        self.message = message
        self.run_result = run_result
        return self
    
    
    
    