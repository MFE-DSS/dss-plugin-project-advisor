import dataikuapi
import pandas as pd
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor


class PluginUsageCheck(InstanceCheck):
    """
    A class used to check that all plugins are used.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the PluginUsageCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics = metrics,
            batch_project_advisor = batch_project_advisor,
            category=InstanceCheckCategory.USAGE,
            name="plugin_usage_check",
            description="Checks all plugins are used at least once."
        )
        self.uses_plugin_usage = True

    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if all plugins are used in at least one project.
        :return: self
        """
        
        check_pass = True
        message = f"All plugins are used at least once."
        result = {}
        nb_plugins_not_used = 0
        plugins_not_used = list()
        
        plugin_list = self.client.list_plugins()
        
        for plugin in plugin_list:
            plugin_id = plugin["id"]
            plugin_usage = self.client.get_plugin(plugin_id).list_usages()
            if not plugin_usage.maybe_used():
                nb_plugins_not_used += 1
                plugins_not_used.append(plugin_id)
                
        if nb_plugins_not_used > 0:
            check_pass = False
            message = f"{nb_plugins_not_used} plugins are not used."
            result.update({"plugins_not_used": plugins_not_used})

        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self