import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.project_check import ProjectCheck




class GlobalTagCheck(ProjectCheck):
    """
    A class used to check if project only uses global tags.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        metrics = List[DSSMetric]
    ):
        """
        Initializes the GlobalTagCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            category=ProjectCheckCategory.DOCUMENTATION,
            name="global_tag_check",
            metrics = metrics
        )

    def run(self) -> ProjectCheck:
        """
        Runs the check to determine if project only uses global tags in: overall project, datasets, dashboards, webapps, recipes.
        :return: self
        """

        # get all global tags on the instance
        inst_tagCat=self.client.get_general_settings().get_raw()["globalTagsCategories"]
        all_global_tags=[]
        for i in inst_tagCat:
            category=i["name"]
            inst_globalTag=i["globalTags"]   
            for j in inst_globalTag:
                text=category + ":" + j["name"]
                all_global_tags.append(text)

        #project tags
        project_tags = self.project.get_metadata()["tags"]

        not_global_project_tags = set(project_tags) - set(all_global_tags)
        project_tags_text= str(not_global_project_tags)
        if len(not_global_project_tags) == 0:
            project_tags_text="None"
        project_tags_result="Non global tags for Project: " + project_tags_text

        #dataset tags
        project_datasets = self.project.list_datasets()
        dataset_tags_result="Non global tags for Datasets: "
        project_datasets_text=""
        for i in project_datasets:
            dataset_tags=i["tags"]

            not_global_dataset_tags = set(dataset_tags) - set(all_global_tags)
            if len(not_global_dataset_tags) > 0:
                project_datasets_text = project_datasets_text + "Dataset '" +i["name"] +"' with tag(s) " + str(not_global_dataset_tags) + ". "

        if len(project_datasets_text) == 0: 
            project_datasets_text="None"
        dataset_tags_result = dataset_tags_result + project_datasets_text

        #Webapp tags
        project_webapps = self.project.list_webapps()
        webapp_tags_result="Non global tags for Webapps: "
        project_webapps_text=""

        for i in project_webapps:

            webapp_tags=i["tags"]

            not_global_webapp_tags = set(webapp_tags) - set(all_global_tags)
            
            if len(not_global_webapp_tags) > 0:
                project_webapps_text = project_webapps_text + " Webapp '" +i["name"] +"' with tag(s) " + str(not_global_webapp_tags) + ". "

        if len(project_webapps_text) == 0: 
            project_webapps_text="None"       
        webapp_tags_result = webapp_tags_result + project_webapps_text

        #Dashboard tags
        project_dashboards = self.project.list_dashboards()
        dashboard_tags_result="Non global tags for Dashboards: "
        project_dashboard_text=""

        for i in project_dashboards:

            dashboard_tags=i["tags"]

            not_global_dashboard_tags = set(dashboard_tags) - set(all_global_tags)
            
            if len(not_global_dashboard_tags) > 0:
                project_dashboard_text = project_dashboard_text + " Dashboard '" +i["name"] +"' with tag(s) " + str(not_global_dashboard_tags) + ". "

        if len(project_dashboard_text) == 0: 
            project_dashboard_text="None"       
        dashboard_tags_result = dashboard_tags_result + project_dashboard_text

        #Recipe tags
        project_recipes = self.project.list_recipes()
        recipes_tags_result="Non global tags for Recipes: "
        project_recipes_text=""

        for i in project_recipes:

            recipes_tags=i["tags"]

            not_global_recipes_tags = set(recipes_tags) - set(all_global_tags)
            
            if len(not_global_recipes_tags) > 0:
                project_recipes_text = project_recipes_text + " Recipe '" +i["name"] +"' with tag(s) " + str(not_global_recipes_tags) + ". "

        if len(project_recipes_text) == 0: 
            project_recipes_text="None"       
        recipes_tags_result = recipes_tags_result + project_recipes_text


        # Summarize results
        if(project_tags_text=="None") and (project_datasets_text=="None") and (project_dashboard_text=="None") and (project_webapps_text=="None") and (project_recipes_text=="None"):
            check_pass = True
        else:
                check_pass = False   

        message= project_tags_result +"\n" + dataset_tags_result +"\n" + dashboard_tags_result +"\n" + webapp_tags_result +"\n" + recipes_tags_result

        result = {}
        result["pass"] = check_pass
        result["message"] = message
        self.check_pass = check_pass
        self.message = message
        self.run_result = result
        return self

