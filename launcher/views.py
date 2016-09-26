import collections
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import boto3

from .models import Profile, Region, AWSResource, EC2LaunchOptionSet
from .awsresource import AWSResourceHandler


# Create your views here.
def index(request):
    profiles = Profile.objects.all()
    regions = Region.objects.all()

    ctx = {
        'profiles': profiles,
        'regions': regions,
    }

    return render(request, "launcher/index.html", ctx)


"""def update_resources(request):
    profile = get_object_or_404(Profile, pk=request.POST.get("profile_id"))
    region = get_object_or_404(Region, request.POST.get("region_id"))
    boto3_session = boto3.Session(profile_name=profile.name)
    arh = AWSResourceHandler(profile.account_id, boto3_session)"""


def ajax_getRegionsForProfile(request, profile_id):
    """Get all available regions for a given profile."""
    regions = get_object_or_404(Profile, pk=profile_id).region_set.all()
    regions = map(Region.to_dict, regions)
    return HttpResponse(json.dumps(regions), content_type="application/json")


def ajax_clearResources(request):
    """Delete all related resources for the given profile & region."""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    awsresources = AWSResource.objects.filter(profile=profile, region=region).order_by("-resource_type")
    for awsresource in awsresources:
        awsresource.delete()
    return HttpResponse("true", content_type="application/json")

def ajax_updateResource(request):
    """Update one resource type for the given profile & region."""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    boto3_session = boto3.Session(profile_name=profile.name, region_name=region.code)
    arh = AWSResourceHandler(profile.account_id, boto3_session)

    resource_type = request.POST.get("resource_type")
    try:
        # look for "update_xxx" method in AWSResourceHandler object:
        func = getattr(arh, "update_"+resource_type)
        # execute update:
        resources = func()
        # convert resource dictionary to AWSResource objects:
        for resource in resources:
            awsresource = AWSResource(
                profile = profile,
                region = region,
                name = resource[0],
                resource_id = resource[1],
                resource_type = resource[2],
                arn = resource[3],
                parent = None
            )
            # VPC doesn't have "parent" resources, just save it to DB:
            if awsresource.resource_type == "vpc":
                awsresource.save()
            # other resources may have a "parent" (VPC):
            elif resource[4] is not None:
                awsresource.parent = AWSResource.objects.get(resource_type="vpc", resource_id=resource[4])
                awsresource.save()
            else:
                awsresource.save()
        return HttpResponse("true", content_type="application/json")
    except AttributeError:
        return HttpResponse("No such resource type", status_code=400)
    

def ajax_listResources(request):
    """Get all AWSResource objects for a given profile & region."""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    awsresources = AWSResource.objects.filter(profile=profile, region=region).order_by("-resource_type")
    seq = map(AWSResource.to_dict, awsresources)
    return HttpResponse(json.dumps(seq), content_type="application/json")


def ajax_listEC2LaunchOptionSets(request):
    """Get all EC2LaunchOptionSet objects for a given profile & region."""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    optionsets = EC2LaunchOptionSet.objects.filter(profile=profile, region=region).order_by('module', 'version')
    seq = map(EC2LaunchOptionSet.to_dict, optionsets)
    return HttpResponse(json.dumps(seq), content_type="application/json")

def ajax_viewEC2LaunchOptionSet(request):
    """Get the detailed information on a given EC2LaunchOptionSet."""
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get("id"))
    return HttpResponse(json.dumps(EC2LaunchOptionSet.to_dict(optionset), indent=2))


def ajax_saveEC2LaunchOptionSet(request):
    """Save EC2LaunchOptionSet with the given Id."""
    # check JSON syntax:
    txt = request.POST.get('content')
    try:
        jsonobj = json.loads(txt)
        txt = json.dumps(jsonobj, indent=2)
    except:
        return HttpResponse("Content is not valid JSON.", status_code=400)
    # load EC2LaunchOptionSet:
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get("id"))
    # save EC2LaunchOptionSet:
    optionset.content = txt
    optionset.save()
    return HttpResponse("true", content_type="application/json")


def ajax_newEC2LaunchOptionSet(request):
    """Create a new EC2LaunchOptionSet"""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    module = request.POST.get('module')
    version = request.POST.get('version')
    az = request.POST.get('az')
    if len(module) * len(version) * len(az) == 0:
        return HttpResponse("false", content_type="application/json")
    # check JSON syntax:
    txt = request.POST.get('content')
    try:
        jsonobj = json.loads(txt)
        txt = json.dumps(jsonobj, indent=2)
    except:
        return HttpResponse("false", content_type="application/json")
    # create the option set:
    try:
        optionset = EC2LaunchOptionSet(
            profile = profile,
            region = region,
            module = module,
            version = version,
            az = az,
            content = txt
        )
        optionset.save()
    except:
        return HttpResponse("false", content_type="application/json")
    return HttpResponse("true", content_type="application/json")


def ajax_listAllImagesForModule(request):
    """List all images for a module."""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('id'))

    module = optionset.module
    images = AWSResource.filter_image_by_module(profile, region, module)
    images = map(AWSResource.to_dict, images)
    return HttpResponse(json.dumps(images), content_type="application/json")