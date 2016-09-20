from django.conf.urls import url

from . import views

urlpatterns = [
    url("^$", views.index, name="index"),
    url("^get_regions_for_profile/(\d+)/$", views.ajax_getRegionsForProfile, name="index"),
]