import dataikuapi

from typing import Any, Dict, List
from abc import ABC
import logging
import socket

from project_advisor.assessments import ProjectCheckCategory


# File to contain the DSSAssessment class implementation.
class DSSAssessmentConfig(ABC):
    """
    Abstract base class for the configuration of DSS Assessments.
    It contains:
    - Filters for all Assessments (checks and metrics)
    - Project & Instance Best Practice Configurations Ex: Check thresholds.
    - Deployment Configurations
    """
    logger: logging.Logger = None
    config: dict = {}
    design_client : dataikuapi.dssclient.DSSClient = None
    
    deployer_client : dataikuapi.dssclient.DSSClient = None
    infra_to_client : Dict[str, dataikuapi.dssclient.DSSClient] = {}
    deployment_method : str = None # custom, fm_managed or manual
    deployment_mode : str = None # local or remote
    project_dependencies : Dict[str, set] = {}
    plugins_usage : Dict[str, set] = {}

    def __init__(self, config: dict, logging_level : str = "WARNING"):
        """
        Initializes the DSSAssessmentConfig with the provided configuration dictionary.
        """
        self.config = config
        self.design_client = self.config.get("design_client", None)
        self.set_logger(logging_level)
        self.logger.info("Initializing the DSS Assessment Config")
        
        check_filters = self.config.get("check_filters", {})
        
        # Deployment pre computations
        project_check_categories = check_filters.get("project_check_categories", [])
        if ProjectCheckCategory.DEPLOYMENT in project_check_categories:
            self.logger.info("Running DEPLOYMENT related computations")
            self.set_deployement_method_and_mode()
            self.logger.debug(f"self.deployment_method : {self.deployment_method}")
            self.logger.debug(f"self.deployment_mode : {self.deployment_mode}")
            if self.deployment_method != None:
                self.set_deployer_client()
                self.set_infra_to_client_mapping()
                self.logger.info("deployer_client and infra_to_client mapping have been created")
            self.compute_project_dependencies()
            
            self.compute_deployments_projects_mapping()
        else:
            self.logger.info("DEPLOYMENT related computations are skipped")
        
        # Plugin Usage pre computation
        if "use_plugin_usage" in check_filters.keys() and check_filters.get("use_plugin_usage", False):
            self.compute_plugins_usage()
        else:
            self.logger.info("Plugin usage related computations are skipped")

    def get_config(self) -> dict:
        return self.config
    
    def set_logger(self, logging_level: str):
        """
        logging_level (String): Optional
        logging levels are : CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
        If no logging level is given, the project variable "logging_level" will be used.
        """
        #Format logging messagae
        formatter = logging.Formatter(fmt='Plugin: Project Advisor | [%(levelname)s] : %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        # Build logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging_level)
        logger.addHandler(handler)

        logger.info(f"logging level set to {logging.getLevelName(logger.getEffectiveLevel())}")
        
        self.logger = logger

        return
    
    
    ### Deployment helper functions ###
    
    def _get_vn_id(self, fm_client :dataikuapi.fmclient.FMClient) -> str:
        """
        Return Virtual Network of current design node
        """
        design_private_ip = socket.gethostbyname(socket.gethostname())
        for instance in fm_client.list_instances():
            if design_private_ip == instance.get_status().get("privateIP", None):
                return instance.instance_data.get("virtualNetworkId", None)
        return None
    
    
    def _get_fm_deployment_config(self, fm_client :dataikuapi.fmclient.FMClient):
        """
        Return FM deployement configuration settings
        """
        vn_id = self._get_vn_id(fm_client)
        vn_data = fm_client.get_virtual_network(vn_id).vn_data 
        managedNodesDirectory = vn_data.get("managedNodesDirectory", False)
        nodesDirectoryDeployerMode = vn_data.get("nodesDirectoryDeployerMode",None)
        return (managedNodesDirectory, nodesDirectoryDeployerMode)
    
    def _get_custom_deployment_mode(self) -> str:
        """
        Fetch the deployment_mode for manually connected Nodes (deployment_method : custom)
        """
        mode = self.design_client.get_general_settings().settings.get("deployerClientSettings", {}).get("mode", None)
        if mode == "LOCAL":
            return "local"
        elif mode == "REMOTE":
            return "remote"
        else:
            return mode

    
    def _get_available_instance_clients_in_vn(self, fm_client :dataikuapi.fmclient.FMClient) -> List[dataikuapi.dssclient.DSSClient]:
        """
        List all of the client for all available (Running) instances managed by the FM in the current Virtual Network.
        """

        instances = fm_client.list_instances()
        vn_id = self._get_vn_id(fm_client)
        instance_clients = []
        for instance in instances:
            if instance.get_status()["cloudMachineIsUp"]== True and instance.instance_data.get("virtualNetworkId") == vn_id:
                client = instance.get_client()
                if not self.config.get("deployment_config",{}).get("verify_ssl_certificate",True):
                    client._session.verify = False
                instance_clients.append(client)
        return instance_clients   
    
    ### Fetch and set the Node Deployment Configuration ###
    
    def set_deployement_method_and_mode(self):
        """
        Set the deployment_method and deployement_mode attributes based on deployment_config. 
        """
        deployment_method = self.config.get("deployment_config", {}).get("deployment_method", None)
        fm_client = self.config.get("deployment_config", {}).get("fm_client", None)
        self.logger.debug(f"deployment_method : {deployment_method}")
        
        if deployment_method == "custom":
            self.deployment_method = "custom"
            self.deployment_mode = self._get_custom_deployment_mode()
        
        elif deployment_method in ["fm-aws", "fm-gcp", "fm-azure"]:
            managedNodesDirectory, nodesDirectoryDeployerMode = self._get_fm_deployment_config(fm_client)
            if managedNodesDirectory:
                if nodesDirectoryDeployerMode == "CENTRAL_DEPLOYER":
                    self.deployment_method = "fm_managed"
                    self.deployment_mode = "remote"

                elif nodesDirectoryDeployerMode == "NO_MANAGED_DEPLOYER":
                    self.deployment_method = "custom" # Doesn't require the FM.
                    self.deployment_mode = self._get_custom_deployment_mode()

                elif nodesDirectoryDeployerMode == "EACH_DESIGN_NODE":
                    self.deployment_method = "fm_managed"
                    self.deployment_mode = "local"
            else:
                self.deployment_method = "fm_managed"
                self.deployment_mode = self._get_custom_deployment_mode()
        
        elif deployment_method == "manual":
            self.deployment_method = "manual"
            self.deployment_mode = None # Not needed
        
        else:
            self.logger.info(f"The deployment method {deployment_method} is not supported OR disabled")
        return
    
    
    ### Setting the deployer client methods ###

    def set_deployer_client(self) -> None:
        """
        Sets the *deployer_client* attribute based on the deployment configurations.
        """
        
        fm_client = self.config.get("deployment_config", {}).get("fm_client", None)

        if self.deployment_method == "custom":
            if self.deployment_mode == "local":
                self.deployer_client = self.design_client
            elif self.deployment_mode == "remote":
                self.deployer_client = self.get_custom_remote_deployer_client(self.design_client)   
            else:
                self.logger.info(f"The deployment mode {self.deployment_mode} is not supported")
        
        elif self.deployment_method == "fm_managed":
            if self.deployment_mode == "local":
                self.deployer_client = self.design_client
            elif self.deployment_mode == "remote":
                self.deployer_client = self.get_fm_remote_deployer_client(fm_client)  
            else:
                self.logger.info(f"The deployment mode {self.deployment_mode} is not supported")
        
        elif self.deployment_method == "manual":
            self.deployer_client = self.config.get("deployment_config", {}).get("manual_deployment", {}).get("deployer_client", None)
        
        else:
            self.logger.info(f"The deployment method {self.deployment_method} is not supported")
        return
       

    def get_custom_remote_deployer_client(self, design_client : dataikuapi.dssclient.DSSClient) -> dataikuapi.dssclient.DSSClient:
        """
        Returns the deployer client for remote & manual deployements.
        """
        self.logger.info(f"Fetching deployer client for customer remote deployment")
        settings = design_client.get_general_settings()
        deployer_settings = settings.settings["deployerClientSettings"]
        
        try:
            host = deployer_settings["nodeUrl"]
            api_key = deployer_settings["apiKey"]
            deployer_client = dataikuapi.DSSClient(host, api_key=api_key)
            
            if not self.config.get("deployment_config",{}).get("verify_ssl_certificate",True):
                    deployer_client._session.verify = False
            
            self.logger.info(f"fetch deployer Instance Id : {deployer_client.get_instance_info().raw['dipInstanceId']}")
            return deployer_client
        
        except:
            self.logger.warning("Failed to load deployer client for this remote custom deployment configuration")
            return None
   
    
    def get_fm_remote_deployer_client(self, fm_client :dataikuapi.fmclient.FMClient) -> dataikuapi.dssclient.DSSClient:
        """
        Return the deployer from a cloud stacks deployment given a Fleet Manager Client. (Assuming there is only one Deployer Node)
        """
        self.logger.info(f"Fetching deployer client for Cloud Stacks remote deployment")
        instance_clients = self._get_available_instance_clients_in_vn(fm_client)

        deployer_client = None
        for client in instance_clients:
            if client.get_instance_info().raw["nodeType"] == "DEPLOYER":
                deployer_client = client
        return deployer_client
    
    
    ### Setting the infra to client mapping functions ###
    
    def set_infra_to_client_mapping(self) -> None:
        """
        Sets the *infra_to_client* attribut regardless of the deployment method.
        """
        fm_client = self.config.get("deployment_config")["fm_client"]    
        
        if self.deployer_client == None:
            self.logger.info("No deployer_client, please set the deployer_client before building the infra_to_client mapping")
            return

        if self.deployment_method == "custom":
            self.infra_to_client = self.get_custom_infra_to_client_mapping()   
        elif self.deployment_method == "fm_managed":
            self.infra_to_client = self.get_fm_infra_to_client_mapping(fm_client)  
        elif self.deployment_method == "manual":
            self.infra_to_client = self.get_manual_infra_to_client_mapping() 
        else:
            self.logger.info(f"The deployment method {self.deployment_method} is not supported")
        return
    
    def get_custom_infra_to_client_mapping(self) -> Dict[str, dataikuapi.dssclient.DSSClient]:
        """
        Returns a mapping between all infras on the deployer and their associated Client for custom deployments.
        """
        self.logger.info(f"Fetching infra clients for custom remote deployment")
        proj_deployer = self.deployer_client.get_projectdeployer()
        infra_to_client = {}
        for infra in proj_deployer.list_infras():
            infra_id = infra.get_settings().settings["id"]
            infra_to_client[infra_id] = None 
            try:
                infra_settings = infra.get_settings().get_raw()
                host = infra_settings["automationNodeUrl"]
                api_key = infra_settings["adminApiKey"]
                client = dataikuapi.DSSClient(host, api_key=api_key)
                if not self.config.get("deployment_config",{}).get("verify_ssl_certificate",True):
                    client._session.verify = False
                infra_to_client[infra_id] = client
            except:
                self.logger.warning("Failed to load automation client for infra : {infra_id}")
        return infra_to_client
 
    
    def get_fm_infra_to_client_mapping(self,fm_client :  dataikuapi.dssclient.DSSClient ) -> Dict[str,dataikuapi.dssclient.DSSClient]:
        """
        Returns a mapping between all infras on the deployer and their associated Client for Cloud Stacks deployments.
        """
        self.logger.info(f"Fetching infra clients for Cloud Stacks remote deployment")
        instance_clients = self._get_available_instance_clients_in_vn(fm_client)
        proj_deployer = self.deployer_client.get_projectdeployer()

        infra_to_client = {}
        for infra in proj_deployer.list_infras():
            infra_id = infra.get_settings().settings["id"]
            infra_node_id = infra.get_settings().settings["nodeId"]
            infra_to_client[infra_id] = None
            for client in instance_clients:
                if client.get_instance_info().raw["nodeType"] == "AUTOMATION":
                    if infra_node_id == client.get_instance_info().raw["nodeId"]:
                        infra_to_client[infra_id] = client
        return infra_to_client
    
    def get_manual_infra_to_client_mapping(self) -> Dict[str, dataikuapi.dssclient.DSSClient]:
        """
        Returns a mapping linking the infra ID and it's client for the test automation node and prod automation node.
        """
        infra_to_client = {}
        dev_auto_client = self.config.get("deployment_config", {}).get("manual_deployment", {}).get("dev_auto_client", None)
        test_auto_client = self.config.get("deployment_config", {}).get("manual_deployment", {}).get("test_auto_client", None)
        prod_auto_client = self.config.get("deployment_config", {}).get("manual_deployment", {}).get("prod_auto_client", None)
        
        try:
            self.deployer_client.get_instance_info()
        except:
            self.logger.info("Deployer client is not reachable, infra clients cannot be fetched")
            return {}
        
        proj_deployer = self.deployer_client.get_projectdeployer()
        for infra in proj_deployer.list_infras():
            stage = infra.get_settings().settings["stage"]
            if stage == "Development":
                infra_to_client.update({infra.id : dev_auto_client})
            elif stage == "Test":
                infra_to_client.update({infra.id : test_auto_client})
            elif stage == "Production":
                infra_to_client.update({infra.id : prod_auto_client})
        return infra_to_client
    
    
    def compute_project_dependencies(self) -> None:
        """
        Update the configuration with the project dependencies.
        """
        try: 
            shared_objects = {}
            project_keys = self.design_client.list_project_keys()

            for sharing_project_key in project_keys:
                project = self.design_client.get_project(sharing_project_key)
                exposed_objects = project.get_settings().get_raw()["exposedObjects"]["objects"]
                for exposed_object in exposed_objects:
                    for rule in exposed_object["rules"]:
                        target_project = rule["targetProject"]
                        if target_project not in shared_objects:
                            shared_objects[target_project] = set()
                        shared_objects[target_project].add(sharing_project_key)

            self.project_dependencies = shared_objects
        except:
            self.project_dependencies = None
        return

    def compute_plugins_usage(self) -> None:
        """
        Returns the usage of plugins for all projects.
        """
        self.logger.info("running plugin usage computation")
        project_plugin_usage = dict()
        plugin_list = self.design_client.list_plugins()
        for plugin in plugin_list:
            plugin_id = plugin["id"]
            plugin_usage = self.design_client.get_plugin(plugin_id).list_usages()
            project_key = 'none'
            for usage in plugin_usage.usages:
                try:
                    # Attempt to access a key that might not exist
                    project_key = usage.project_key
                except KeyError:
                    pass
                
                project_plugin_usage.setdefault(project_key, set()).add(plugin_id)
                
        self.plugins_usage = project_plugin_usage
        return 
    
    def compute_deployments_projects_mapping(self) -> None:
        """
        Returns the mapping between design and deployment project keys.
        """
        deployment_project_mapping = dict()
        try:
            deployments = self.deployer_client.get_projectdeployer().list_deployments()
            for deployment in deployments:
                deployments_info = deployment.get_status().get_light()
                design_project_key = deployments_info["packages"][-1]["designNodeInfo"]["projectKey"]
                deployed_project_key = deployments_info["deploymentBasicInfo"]["deployedProjectKey"]
                deployment_project_mapping.setdefault(design_project_key, list()).append(deployed_project_key)

            self.deployment_project_mapping = deployment_project_mapping
        except:
            self.deployment_project_mapping = None
        return 
    

                             