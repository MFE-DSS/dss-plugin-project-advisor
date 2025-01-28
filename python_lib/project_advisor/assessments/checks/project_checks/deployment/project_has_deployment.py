import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck


class ProjectHasDeploymentCheck(ProjectCheck):
    """
    A class used to check if a project has at least one deployment on the deployer.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the ProjectHasDeploymentCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DEPLOYMENT,
            name="project_has_deployment_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project has at least one deployment on the deployer.
        :return: self
        """
        self.config.logger.debug(f"Running project_has_deployment_check in {self.project.project_key}")
        
        check_pass = False
        message = f"Project {self.project.project_key} doesn't have a deployment on the deployer"
        run_result = {}
        
        try:
            self.config.deployer_client.get_instance_info()
           
            deployer = self.config.deployer_client.get_projectdeployer()
            deployment_ids = []
            for deployment in deployer.list_deployments():
                if deployment.get_settings().get_raw()["publishedProjectKey"] ==self.project.project_key:
                    deployment_ids.append(deployment.get_settings().get_raw()["id"])
                    check_pass = True
                    message = f"Project {self.project.project_key} has a deployment on the deployer"

            run_result["deployment_ids"] = deployment_ids

        except Exception as error:
            check_pass = ""
            message = "Deployment best practices can't be checked with the current deployer configuration" 
            run_result = {
                            "error" : type(error).__name__,
                            "error_message" : str(error)
                         }
        

        self.check_pass = check_pass
        self.message = message
        self.run_result = run_result
        return self
    
    
    
    