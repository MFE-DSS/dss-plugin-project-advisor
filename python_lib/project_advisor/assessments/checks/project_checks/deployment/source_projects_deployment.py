import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ProjectHasSourceDeployedCheck(ProjectCheck):
    """
    A class used to check if a project has all source projects published and deployed.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectHasSourceDeployedCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DEPLOYMENT,
            name="check_project_has_source_deployed",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project has all source projects in the deployer and the automation infrastructures.
        :return: self
        """
        
        project_key = self.project.project_key
        self.config.logger.debug(f"Running project_has_source_deployed in {project_key}")
        
        check_pass = True
        message = f"Project {project_key} has all source projects published and deployed"
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
            # Compute the shared objects across the project and the instance
            shared_objects = {}
            try:
                project_keys = self.client.list_project_keys()

                # Check that the project dependencies are not already computed
                if self.config.project_dependencies is None:
                    for sharing_project_key in project_keys:
                        project = self.client.get_project(sharing_project_key)
                        exposed_objects = project.get_settings().get_raw()["exposedObjects"]["objects"]
                        for exposed_object in exposed_objects:
                            for rule in exposed_object["rules"]:
                                target_project = rule["targetProject"]
                                if target_project not in shared_objects:
                                    shared_objects[target_project] = set()
                                shared_objects[target_project].add(sharing_project_key)
                else:
                    shared_objects = self.config.project_dependencies
            except Exception as e:
                self.check_pass = None
                self.message = "This check requires admin rights."
                return self

            if project_key not in shared_objects:
                message = "No shared object in this project."
            else:
                # Retrieve projects on the deployer and the infrastructures
                project_deployer = self.config.deployer_client.get_projectdeployer()
                deployer_projects = [deployer_project.project_key for deployer_project in project_deployer.list_projects()]
                infra_projects = {infra_id: infra_client.list_project_keys() for infra_id, infra_client in self.config.infra_to_client.items()}
                
                # Retrieve the projects sharing objets to the current project
                sharing_projects = shared_objects[project_key]
                
                # Check whether source projects are not published and/or deployed
                for sharing_project in sharing_projects:
                    if sharing_project not in deployer_projects:
                        deployer_projects_to_publish.append(sharing_project)
                    for infra_id, infra_project in infra_projects.items():
                        if sharing_project not in infra_project:
                            if infra_id not in infra_projects_to_deploy:
                                infra_projects_to_deploy[infra_id] = list()
                            infra_projects_to_deploy[infra_id].append(sharing_project)
                
                if deployer_projects_to_publish:
                    check_pass = False
                    message = f"Source projects are not all published for project {project_key}."  
                    run_result["source_projects_to_publish"] = deployer_projects_to_publish

                if infra_projects_to_deploy:
                    check_pass = False
                    message = f"Source projects are not all deployed for project {project_key}."
                    run_result["source_projects_to_deploy_by_infra"] = infra_projects_to_deploy

        self.check_pass = check_pass
        self.message = message
        self.run_result = run_result
        return self
    
    
    
    