# This file is the code for the plugin Python step project-advisor
import dataiku
from datetime import datetime
import logging
import re

from dataiku.customstep import get_plugin_config
from dataiku.customstep import get_step_config
from dataiku.customstep import get_step_resource

from project_advisor.advisors.project_advisor import ProjectAdvisor

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder

from project_advisor.report.project_report import ProjectReportDashboardGenerator


# Load scenario (as this is a sceanrio step)
from dataiku.scenario import Scenario
scenario = Scenario()

### INITIALISATION 
client = dataiku.api_client()
default_project = client.get_default_project()
project = default_project

resource_folder = get_step_resource()
plugin_config = get_plugin_config()
step_config = get_step_config()


# Load component specific parameters
override_default_project = step_config.get("override_default_project",False)
project_key = step_config.get("project_key",None)
check_report_dataset_name = step_config.get("check_report_dataset",None)
metric_report_dataset_name = step_config.get("metric_report_dataset",None)
check_project_score = step_config.get("check_project_score",False)
project_score_threshold = step_config.get("project_score_threshold",None)
generate_dashboard_project_report = step_config.get("generate_dashboard_project_report",False)

### Build the Project Advisor ###

# Override default project
if override_default_project:
    pattern = re.compile("^(\${)+.*}")   
    if (pattern.match(project_key)):
        var_name = project_key[2:-1]
        var_value = dataiku.get_custom_variables().get(var_name, None)
        if (var_value != None):
            project_key = str(var_value)
        else:
            raise Exception("Project variable : {}, does not exist for this project".format(var_name))
    print (f"project_key : {project_key}")
    project = client.get_project(project_key)

# Creating Logging connections
check_report_dataset = dataiku.Dataset(check_report_dataset_name)
metric_report_dataset = dataiku.Dataset(metric_report_dataset_name)

assessment_config = DSSAssessmentConfigBuilder.build_from_scenario_step_config(resource_folder = resource_folder, 
                                                                               plugin_config = plugin_config, 
                                                                               step_config = step_config )
# KEEP COMMENTED
#assessment_config.logger.debug(f"resource_folder {resource_folder}")
#assessment_config.logger.debug(f"plugin_config {plugin_config}")
#assessment_config.logger.debug(f"step_config {step_config}")

assessment_config.logger.info("Building and running Project Advisor")
project_advisor = ProjectAdvisor(client = client, 
                                 config = assessment_config, 
                                 project = project,
                                 check_report_dataset = check_report_dataset,
                                 metric_report_dataset = metric_report_dataset)


# Run the ProjectAdvisor and save the results.
project_advisor.run()
project_advisor.save()

# Generate a Dashboard report if activated.
if generate_dashboard_project_report:
    project_dashboard_generator = ProjectReportDashboardGenerator(project = project, 
                                check_dataset = check_report_dataset,
                                metric_dataset = metric_report_dataset)
    project_dashboard_generator.generate()

# Compute project score & project status
project_score = project_advisor.get_score()
project_status = project_advisor.get_status()
pat_vars = {
                "pat_score" : project_score,
                "pat_status" : project_status
             }

# Set project score & status as project variable
v = default_project.get_variables()
v["standard"].update(pat_vars)
default_project.set_variables(v)

# Set project score & status as scenario variable
scenario.set_scenario_variables(**pat_vars)

# Raise error if project score is less than threshold (if project score should be checked)
if check_project_score:
    if project_score < project_score_threshold:
        raise Exception(f"The project score of {project_score} is less than the project threshold of {project_score_threshold}")




