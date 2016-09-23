from django.conf.urls import url

from . import views

urlpatterns = [
    url("^$", views.index, name="index"),
    url("^get_regions_for_profile/(\d+)/$", views.ajax_getRegionsForProfile, name="ajax_getRegionsForProfile"),
    url("^update_resource/", views.ajax_updateResource, name="ajax_updateResource"),
    url("^list_resources/", views.ajax_listResources, name="ajax_listResources"),
    url("^clear_resources/", views.ajax_clearResources, name="ajax_clearResources"),
    url("^list_ec2launchoptionsets/", views.ajax_listEC2LaunchOptionSets, name="ajax_listEC2LaunchOptionSets"),
]