import collections
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import boto3

from .models import Profile, Region, AWSResource, EC2LaunchOptionSet
from .awsresource import AWSResourceHandler
from .ec2 import run_instances, find_name_tag, add_instance_tags, add_volume_tags


# Create your views here.
def index(request):
    profiles = Profile.objects.all()
    regions = Region.objects.all()

    ctx = {
        'profiles': profiles,
        'regions': regions,
    }

    return render(request, "launcher/index.html", ctx)


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
        return HttpResponse("No such resource type", status=400)
    

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
    optionsets = EC2LaunchOptionSet.objects\
        .filter(profile=profile, region=region, enabled=True)\
        .order_by('module', 'version')
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
        return HttpResponse("Content is not valid JSON.", status=400)
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
            content = txt,
            enabled = True
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


def ajax_updateEC2LaunchOptionSet(request):
    """Update an existing EC2LaunchOptionSet with a new AMI."""
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('id'))
    new_image = get_object_or_404(AWSResource, pk=request.POST.get('image_id'))
    # data validation:
    profile = optionset.profile
    region = optionset.region
    if profile != new_image.profile or region != new_image.region:
        return HttpResponse("false", status=400)
    try:
        # get and update new version:
        new_version = AWSResource.get_image_version(new_image.name)
        optionset.version = new_version
        # update "image" attribute:
        attr_image = [new_image.name, new_image.resource_id]
        attr_dict = json.loads(optionset.content)
        attr_dict.update({"image": attr_image})
        optionset.content = json.dumps(attr_dict, indent=2)
        # remove pk and save as a new one:
        optionset.pk = None
        optionset.save()
        return HttpResponse("true", content_type="application/json")
    except Exception as ex:
        return HttpResponse(json.dumps(ex.message), content_type="application/json")


def ajax_runInstances(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    count = int(request.POST.get('count'))
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")
    instance_ids = run_instances(ec2resource, optionset, count)
    return HttpResponse(json.dumps(instance_ids), content_type="application/json")


def ajax_addInstanceTags(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    instance_ids = request.POST.getlist('instance_ids[]')
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")
    result = add_instance_tags(ec2resource, optionset, instance_ids)
    return HttpResponse(json.dumps(result), content_type="application/json")

def ajax_addVolumeTags(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    instance_ids = request.POST.getlist('instance_ids[]')
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")
    result = add_volume_tags(ec2resource, instance_ids)
    return HttpResponse(json.dumps(result), content_type="application/json")