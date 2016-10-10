from django.conf.urls import url

from . import views

app_name = "launcher"
urlpatterns = [
    url("^$", views.index, name="index"),
    url("^get_regions_for_profile/(\d+)/$", views.ajax_getRegionsForProfile, name="ajax_getRegionsForProfile"),
    url("^update_resource/", views.ajax_updateResource, name="ajax_updateResource"),
    url("^list_resources/", views.ajax_listResources, name="ajax_listResources"),
    url("^clear_resources/", views.ajax_clearResources, name="ajax_clearResources"),
    url("^list_ec2launchoptionsets/", views.ajax_listEC2LaunchOptionSets, name="ajax_listEC2LaunchOptionSets"),
    url("^view_ec2launchoptionset/", views.ajax_viewEC2LaunchOptionSet, name="ajax_viewEC2LaunchOptionSet"),
    url("^save_ec2launchoptionset/", views.ajax_saveEC2LaunchOptionSet, name="ajax_saveEC2LaunchOptionSet"),
    url("^new_ec2launchoptionset/", views.ajax_newEC2LaunchOptionSet, name="ajax_newEC2LaunchOptionSet"),
    url("^update_ec2launchoptionset/", views.ajax_updateEC2LaunchOptionSet, name="ajax_updateEC2LaunchOptionSet"),
    url("^delete_ec2launchoptionset/", views.ajax_deleteEC2LaunchOptionSet, name="ajax_deleteEC2LaunchOptionSet"),
    url("^list_all_images_for_module/", views.ajax_listAllImagesForModule, name="ajax_listAllImagesForModule"),
    url("^run_instances/", views.ajax_runInstances, name="ajax_runInstances"),
    url("^add_instance_tags/", views.ajax_addInstanceTags, name="ajax_addInstanceTags"),
    url("^add_volume_tags/", views.ajax_addVolumeTags, name="ajax_addVolumeTags"),
    url("^list_instances_for_ec2launchoptionset/", views.ajax_listInstancesForEC2LaunchOptionSet, name="ajax_listInstancesForEC2LaunchOptionSet"),
    url("^start_instance/", views.ajax_startInstance, name="ajax_startInstance"),
    url("^stop_instance/", views.ajax_stopInstance, name="ajax_stopInstance"),
    url("^terminate_instance/", views.ajax_terminateInstance, name="ajax_terminateInstance"),
    url("^stop_all_instances/", views.ajax_stopAllInstances, name="ajax_stopAllInstances"),
]