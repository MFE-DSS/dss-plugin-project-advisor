import dataiku
import dataikuapi

from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments import (ProjectCheckCategory, InstanceCheckCategory)

class DSSAssessmentConfigBuilder():
    

    @classmethod
    def build_from_macro_config(cls, config : dict = {}, plugin_config : dict = {}):
        """
        Input : Macro component settings
        Output : DSSAssessmentConfig
        Build the DSSAssessmentConfig
        """
        client = dataiku.api_client()
        
        ### Loading parameters ###

        # Project & Instance Check Filters
        project_check_filter_preset = config.get("project_check_filter_preset",{})
        llm_id = project_check_filter_preset.get("llm_id",None)
        instance_check_filter_preset = config.get("instance_check_filter_preset",{})
        check_filters = DSSAssessmentConfigBuilder.build_check_filters(project_check_filter_preset, instance_check_filter_preset)
        
        # Project & Instance Check Configs
        project_check_config_preset = config.get("project_check_config_preset",{})
        logging_level = project_check_config_preset.get("logging_level","DEBUG")
        instance_check_config_preset = config.get("instance_check_config_preset",{})
        check_configs = DSSAssessmentConfigBuilder.build_check_configs(project_check_config_preset, instance_check_config_preset)
        
        # Deployment Settings
        deployment_config = DSSAssessmentConfigBuilder.build_deployment_config(plugin_config)
        
        if not deployment_config["verify_ssl_certificate"]:
            client._session.verify = False

        ### Defining the final DSSAssessemntConfig
        return DSSAssessmentConfig({
             "design_client" : client,
             "deployment_config" : deployment_config,
             "check_filters" : check_filters,
             "check_configs" : check_configs,
            "llm_id":llm_id, # Keep top level
            }, 
            logging_level)
    
    @classmethod
    def build_check_configs(clf, project_check_config_preset : dict, instance_check_config_preset : dict):
        """
        Input : plugin_config : dict of plugin level configs 
        Output : dict of deployment config
        Helper function to build the check_configs.
        """
        
        # Project Check filters
        max_datasets_per_flow_zone = project_check_config_preset.get("max_datasets_per_flow_zone",None)
        max_datasets_per_flow = project_check_config_preset.get("max_datasets_per_flow",None)
        max_nbr_row_python_recipe = project_check_config_preset.get("max_nbr_row_python_recipe",None)
        max_nbr_row_python_webapp = project_check_config_preset.get("max_nbr_row_python_webapp",None)
        max_nbr_steps_in_scenarios = project_check_config_preset.get("max_nbr_steps_in_scenarios",None)
        max_groups_users_sharing = project_check_config_preset.get("max_groups_users_sharing",None)
        min_scenario_trigger_time_period = project_check_config_preset.get("min_scenario_trigger_time_period",None)
        max_nbr_top_level_steps_prepare_recipe = project_check_config_preset.get("max_nbr_top_level_steps_prepare_recipe",None)
        
        critical_project_check_list = project_check_config_preset.get("critical_project_check_list",[])
        
        # Instance Check Filter preset parameters 
        max_nbr_sanity_warnings = instance_check_config_preset.get("max_nbr_sanity_warnings",None)
        
        
        # Build Assessment filter config
        check_configs = {
                             # Project Check Configs
                             "max_datasets_per_flow_zone": max_datasets_per_flow_zone,
                             "max_datasets_per_flow" : max_datasets_per_flow,
                             "max_nbr_row_python_recipe": max_nbr_row_python_recipe,
                             "max_nbr_row_python_webapp": max_nbr_row_python_webapp,
                             "max_nbr_steps_in_scenarios": max_nbr_steps_in_scenarios,
                             "max_groups_users_sharing": max_groups_users_sharing,
                             "min_scenario_trigger_time_period" : min_scenario_trigger_time_period,
                             "max_nbr_top_level_steps_prepare_recipe": max_nbr_top_level_steps_prepare_recipe,
                             "critical_project_check_list" : critical_project_check_list,
                             
                             # Instance Check configs
                             "max_nbr_sanity_warnings":max_nbr_sanity_warnings,
                        }
        
        return check_configs    

    
    
    @classmethod
    def build_check_filters(clf, project_check_filter_preset : dict, instance_check_filter_preset : dict):
        """
        Input : plugin_config : dict of plugin level configs 
        Output : dict of deployment config
        Helper function to build the check_filters
        """
        
        # Project Check Filters
        llm_id = project_check_filter_preset.get("llm_id",None)
        use_llm = project_check_filter_preset.get("use_llm",None)
        
        use_plugin_usage = project_check_filter_preset.get("use_plugin_usage",None)
        use_fs = project_check_filter_preset.get("use_fs",None)
        
        use_project_check_white_list = project_check_filter_preset.get("use_project_check_white_list",False)
        project_check_white_list = project_check_filter_preset.get("project_check_white_list",[])
        
        project_check_categories = project_check_filter_preset.get("project_check_categories",[])
        project_check_categories = [ProjectCheckCategory[category] for category in project_check_categories]
        
        # Instance Check Filter preset parameters 
        instance_check_categories = instance_check_filter_preset.get("instance_check_categories",[])
        instance_check_categories = [InstanceCheckCategory[category] for category in instance_check_categories]
        
        
        # Build Assessment filter config
        check_filters = {
                            "use_llm" : use_llm,
                            "use_fs" : use_fs,
                            "use_plugin_usage" : use_plugin_usage,
                            "use_project_check_white_list" : use_project_check_white_list,
                            "project_check_white_list" : project_check_white_list,
                            "project_check_categories" : project_check_categories,
                            "instance_check_categories": instance_check_categories
                        }
        
        return check_filters
        
        
    
    
    @classmethod
    def build_deployment_config(clf, plugin_config : dict):
        """
        Input : plugin_config : dict of plugin level configs 
        Output : return : dict of deployment config
        Helper function to build the deployment_config
        """
        
        # Plugin (Instance) level config
        deployment_method = plugin_config.get("deployment_method", None)
        fm_host = plugin_config.get("fm_host", None)
        fm_api_key_id = plugin_config.get("fm_api_key_id", None)
        fm_api_key_secret = plugin_config.get("fm_api_key_secret", None)
        verify_ssl_certificate = plugin_config.get("verify_ssl_certificate", True)
        
        # For manual definition of deployer, test-auto & auto
        deployer_host = plugin_config.get("deployer_host", None)
        deployer_api_key = plugin_config.get("deployer_api_key", None)
        
        has_dev_auto_node = plugin_config.get("has_dev_auto_node", False)
        dev_auto_host = plugin_config.get("dev_auto_host", None)
        dev_auto_api_key = plugin_config.get("dev_auto_api_key", None)

        has_test_auto_node = plugin_config.get("has_test_auto_node", False)
        test_auto_host = plugin_config.get("test_auto_host", None)
        test_auto_api_key = plugin_config.get("test_auto_api_key", None)

        has_prod_auto_node = plugin_config.get("has_prod_auto_node", False)
        prod_auto_host = plugin_config.get("prod_auto_host", None)
        prod_auto_api_key = plugin_config.get("prod_auto_api_key", None)
        
        ### Build Assessment deployment config
        fm_client = None
        manual_deployment = {}
        if deployment_method == "fm-azure":
            fm_client = dataikuapi.fmclient.FMClientAzure(fm_host, fm_api_key_id, fm_api_key_secret)

        elif deployment_method == "fm-aws":
            fm_client = dataikuapi.fmclient.FMClientAWS(fm_host, fm_api_key_id, fm_api_key_secret)

        elif deployment_method == "fm-gcp":
            fm_client = dataikuapi.fmclient.FMClientGCP(fm_host, fm_api_key_id, fm_api_key_secret)

        elif deployment_method == "manual":
            # Manually entered deployer
            deployer_client = dataikuapi.DSSClient(host=deployer_host, api_key=deployer_api_key)
            if not verify_ssl_certificate:
                deployer_client._session.verify = False
            manual_deployment["deployer_client"] =  deployer_client

            # Manually entered dev auto
            if has_dev_auto_node:
                dev_auto_client = dataikuapi.DSSClient(host=dev_auto_host, api_key=dev_auto_api_key)
                if not verify_ssl_certificate:
                    dev_auto_client._session.verify = False
                manual_deployment["dev_auto_client"] =  dev_auto_client

            # Manually entered test auto
            if has_test_auto_node:
                test_auto_client = dataikuapi.DSSClient(host=test_auto_host, api_key=test_auto_api_key)
                if not verify_ssl_certificate:
                    test_auto_client._session.verify = False
                manual_deployment["test_auto_client"] =  test_auto_client

            # Manually entered prod auto
            if has_prod_auto_node:
                prod_auto_client = dataikuapi.DSSClient(host=prod_auto_host, api_key=prod_auto_api_key)
                if not verify_ssl_certificate:
                    prod_auto_client._session.verify = False
                manual_deployment["prod_auto_client"] =  prod_auto_client

        if not verify_ssl_certificate and fm_client != None:
            fm_client._session.verify = False

        deployment_config = {"deployment_method" : deployment_method,
                             "manual_deployment" : manual_deployment,
                             "fm_client" : fm_client,
                             "verify_ssl_certificate" : verify_ssl_certificate
        }
        return deployment_config
    
    
    
    @classmethod
    def build_from_scenario_step_config(cls, resource_folder : str = "", plugin_config : dict = {}, step_config : dict = {}):
        """
        Input : Scenario step component settings
        Output : DSSAssessmentConfig
        Build the DSSAssessmentConfig
        """
        
        ### Loading parameters ###
        client = dataiku.api_client()

        ### Load component specific parameters ###
        check_report_dataset_name = step_config.get("check_report_dataset",None)
        metric_report_dataset_name = step_config.get("metric_report_dataset",None)
        project_score_threshold = step_config.get("project_score_threshold",None)
        generate_dashboard_project_report = step_config.get("generate_dashboard_project_report",False)

        ### Build the Project Advisor ###

        # Creating Logging connections
        check_report_dataset = dataiku.Dataset(check_report_dataset_name)
        metric_report_dataset = dataiku.Dataset(metric_report_dataset_name)


         # Project Check Filters
        project_check_filter_preset = plugin_config.get("config",{}).get("project_check_filter_preset", None)
        llm_id = project_check_filter_preset.get("llm_id",None)
        check_filters = DSSAssessmentConfigBuilder.build_check_filters(project_check_filter_preset, {})
        
        # Project Check Configs
        project_check_config_preset = plugin_config.get("config",{}).get("project_check_config_preset", {})
        logging_level = project_check_config_preset.get("logging_level","INFO")
        check_configs = DSSAssessmentConfigBuilder.build_check_configs(project_check_config_preset, {})
        
        # Deployment Settings
        plugin_level_config = plugin_config.get("pluginConfig",{})
        deployment_config = DSSAssessmentConfigBuilder.build_deployment_config(plugin_level_config)
        print (f"deployment_config : {deployment_config}")
        
        if not deployment_config["verify_ssl_certificate"]:
            client._session.verify = False
        
        ### Defining the final DSSAssessemntConfig
        return DSSAssessmentConfig({
                                 "design_client" : client,
                                 "deployment_config" : deployment_config,
                                 "check_filters" : check_filters,
                                 "check_configs" : check_configs,
                                 "llm_id":llm_id # keep top level
                                }, logging_level)
        
        
        
        
    