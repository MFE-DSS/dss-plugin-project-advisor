import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck



class ProjectSharedGroupsCheck(ProjectCheck):
    """
    A class used to check if the project is shared to no more than X groups or users.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics: List[DSSMetric],
    ):
        """
        Initializes the ProjectSharedGroupsCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.ROBUSTNESS,
            name="project_shared_max_groups_users",
            description="A class used to check if the project is shared to no more than X groups or users.",
            metrics=metrics,
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if the project is shared to no more than X groups or users.
        :return : self
        """
        config = self.config.get_config()["check_configs"]
        max_groups_users_sharing = config["max_groups_users_sharing"]
        
        project_permissions = self.project.get_permissions().get("permissions")

        groups = [permission["group"] for permission in project_permissions if "group" in permission]
        users = [permission["user"] for permission in project_permissions if "user" in permission]
        
        n_groups = len(groups)
        n_users = len(users)
        
        check_pass = True
        message = f"Project is shared with {n_groups + n_users} groups or users."

        if (n_groups + n_users) > max_groups_users_sharing:
            check_pass = False
            message = f"Project is shared with more than {max_groups_users_sharing} groups or users."

        if n_groups == 0 and n_users == 0:
            check_pass = False
            message = "Project wasn't shared with anyone."
        
        result = {"users": users, "groups": groups}

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self