import collections
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import boto3

from .models import Profile, Region, AWSResource
from .awsresource import AWSResourceHandler

# Create your views here.
def index(request):
    profiles = Profile.objects.all()
    regions = Region.objects.all()

    modules = {
        "account": [
            ["account", "1.1.1", "aps1", "a"],
            ["account", "1.1.2", "aps1", "a"],
        ],
        "connector": [
            ["connector", "2.0.8", "aps1", "a"],
            ["connector", "2.0.9", "aps1", "a"],
        ],
        "device": [
            ["device", "2.1.12", "aps1", "a"],
            ["device", "2.1.13", "aps1", "a"],
        ],
        "appservice_pushservice": [
            ["appservice_pushservice", "1.0.0_1.0.0", "aps1", "a"],
            ["appservice_pushservice", "1.0.1_1.0.1", "aps1", "a"],
        ]

    }
    ctx = {
        'profiles': profiles,
        'regions': regions,
        'modules': modules,
    }
    return render(request, "launcher/index.html", ctx)

def ajax_getRegionsForProfile(request, profile_id):
    regions = get_object_or_404(Profile, pk=profile_id).region_set.all()
    regions = map(Region.to_dict, regions)
    return HttpResponse(json.dumps(regions), content_type="application/json")

def update_resources(request):
    profile = get_object_or_404(Profile, pk=request.POST.get("profile_id"))
    region = get_object_or_404(Region, request.POST.get("region_id"))
    boto3_session = boto3.Session(profile_name=profile.name)
    arh = AWSResourceHandler(profile.account_id, boto3_session)
    