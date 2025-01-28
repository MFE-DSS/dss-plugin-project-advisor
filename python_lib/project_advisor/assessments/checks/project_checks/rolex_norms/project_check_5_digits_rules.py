
import re
import dataikuapi


#python-lib\project_advisor\assessments\checks\project_checks\rolex_norms

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.checks.project_check import ProjectCheck
from project_advisor.assessments.config import DSSAssessmentConfig



class ProjectKeyFormatCheck(ProjectCheck):
    """
    Check that the project key is in the format of 5 alphanumeric characters.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics : list[DSSMetric]
    ):
        """
        Initialize with the rule to check project key format.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.FLOW,
            name="project_key_format_check",
            description="Check that the project key is in the format of 5 alphanumeric characters",
            metrics=metrics,
            # V12 by default
            #dss_version_min=Version("12.0.0"),
            #dss_version_max=None # No upper limit
        )

    def run(self) -> ProjectCheck:
        """
        Run the check for project key format
        :return: self
        """
        project_key = self.project.project_key
        is_valid_format = bool(re.match(r'^[a-zA-Z0-9]{5}$', project_key))

        # Determine the pass/fail status
        self.check_pass = is_valid_format
        self.message = "Project key is in valid format" if is_valid_format else "Project key is not in valid format"
        self.run_result = {"project_key": project_key}
        return self
