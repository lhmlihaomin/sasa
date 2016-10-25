import collections
import json
import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import boto3

from .models import Profile, Region, AWSResource, EC2LaunchOptionSet
from .awsresource import AWSResourceHandler
from .ec2 import run_instances, find_name_tag, add_instance_tags, \
add_volume_tags, get_instances_for_ec2launchoptionset

# logger:
logger = logging.getLogger('django')

def JSONResponse(obj):
    return HttpResponse(json.dumps(obj), content_type="application/json")

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
    regions = list(map(Region.to_dict, regions))
    return JSONResponse(regions)


def ajax_clearResources(request):
    """Delete all related resources for the given profile & region."""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    awsresources = AWSResource.objects.filter(profile=profile, region=region).order_by("-resource_type")

    logger.info("clearResources: %s, %s"%(profile.name, region.name))

    for awsresource in awsresources:
        awsresource.delete()
    logger.info("clearResources: DONE.")
    return JSONResponse(True)

def ajax_updateResource(request):
    """Update one resource type for the given profile & region."""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    boto3_session = boto3.Session(profile_name=profile.name, region_name=region.code)
    arh = AWSResourceHandler(profile.account_id, boto3_session)
    resource_type = request.POST.get("resource_type")

    logger.info("updateResource: %s, %s, %s"%(profile.name, region.name, resource_type))

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
        logger.info("updateResource: DONE.")
        return JSONResponse(True)
    except AttributeError:
        logger.error("updateResource: no such resource type: %s"%(resource_type))
        return HttpResponse("No such resource type", status=400)
    

def ajax_listResources(request):
    """Get all AWSResource objects for a given profile & region."""
    profile = get_object_or_404(Profile, pk=request.GET.get('profile_id'))
    region = get_object_or_404(Region, pk=request.GET.get('region_id'))
    awsresources = AWSResource.objects.filter(profile=profile, region=region).order_by("-resource_type")
    seq = list(map(AWSResource.to_dict, awsresources))
    return JSONResponse(seq)


def ajax_listEC2LaunchOptionSets(request):
    """Get all EC2LaunchOptionSet objects for a given profile & region."""
    profile = get_object_or_404(Profile, pk=request.GET.get('profile_id'))
    region = get_object_or_404(Region, pk=request.GET.get('region_id'))
    optionsets = EC2LaunchOptionSet.objects\
        .filter(profile=profile, region=region, enabled=True)\
        .order_by('module', 'version')
    seq = list(map(EC2LaunchOptionSet.to_dict, optionsets))
    return JSONResponse(seq)

def ajax_viewEC2LaunchOptionSet(request):
    """Get the detailed information on a given EC2LaunchOptionSet."""
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.GET.get("id"))
    return HttpResponse(json.dumps(EC2LaunchOptionSet.to_dict(optionset), indent=2))


def ajax_saveEC2LaunchOptionSet(request):
    """Save EC2LaunchOptionSet with the given Id."""
    txt = request.POST.get('content')
    # load EC2LaunchOptionSet:
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get("id"))
    
    logger.info("saveEC2LaunchOptionSet: %s, %s, %s"%(
        optionset.profile.name,
        optionset.region.name,
        optionset.name))

    # check JSON syntax:
    try:
        jsonobj = json.loads(txt)
        txt = json.dumps(jsonobj, indent=2)
    except Exception as ex:
        logger.error("saveEC2LaunchOptionSet: %s"%(ex.message))
        return HttpResponse("Content is not valid JSON.", status=400)
    # save EC2LaunchOptionSet:
    optionset.content = txt
    optionset.save()
    logger.info("saveEC2LaunchOptionset: DONE.")
    return JSONResponse(True)


def ajax_newEC2LaunchOptionSet(request):
    """Create a new EC2LaunchOptionSet"""
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    module = request.POST.get('module')
    version = request.POST.get('version')
    az = request.POST.get('az')

    logger.info("newEC2LaunchOptionSet: %s, %s, %s-%s-%s"%(
        profile.name,
        region.name,
        module,
        version,
        az
    ))

    if len(module) * len(version) * len(az) == 0:
        return JSONResponse(False)
    # check JSON syntax:
    txt = request.POST.get('content')
    try:
        jsonobj = json.loads(txt)
        txt = json.dumps(jsonobj, indent=2)
    except Exception as ex:
        logger.error("newEC2LaunchOptionset: %s"%(ex.message))
        return JSONResponse(False)
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
    except Exception as ex:
        logger.error("newEC2LaunchOptionset: %s"%(ex.message))
        return JSONResponse(False)
    logger.info("newEC2LaunchOptionset: DONE.")
    return JSONResponse(True)


def ajax_listAllImagesForModule(request):
    """List all images for a module."""
    profile = get_object_or_404(Profile, pk=request.GET.get('profile_id'))
    region = get_object_or_404(Region, pk=request.GET.get('region_id'))
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.GET.get('id'))

    module = optionset.module
    images = AWSResource.filter_image_by_module(profile, region, module)
    images = list(map(AWSResource.to_dict, images))
    return JSONResponse(images)


def ajax_updateEC2LaunchOptionSet(request):
    """Update an existing EC2LaunchOptionSet with a new AMI."""
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('id'))
    new_image = get_object_or_404(AWSResource, pk=request.POST.get('image_id'))
    # data validation:
    profile = optionset.profile
    region = optionset.region

    logger.info("updateEC2LaunchOptionSet: %s, %s, %s, %s"%(
        profile.name,
        region.name,
        optionset.name,
        new_image
    ))

    if profile != new_image.profile or region != new_image.region:
        logger.error("updateEC2LaunchOptionSet: profile/region doesn't match.")
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
        logger.info("updateEC2LaunchOptionSet: DONE.")
        return JSONResponse(True)
    except Exception as ex:
        logger.error("updateEC2LaunchOptionSet: %s"%(ex.message,))
        return JSONResponse(ex.message)


def ajax_deleteEC2LaunchOptionSet(request):
    """Delete an EC2LaunchOptionSet."""
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    logger.info("deleteEC2LaunchOptionSet: %s"%(optionset.name))
    try:
        optionset.delete()
    except Exception as ex:
        logger.error("deleteEC2LaunchOptionSet: %s"%(ex.message))
        return JSONResponse(False)
    logger.info("deleteEC2LaunchOptionSet: DONE.")
    return JSONResponse(True)


    
def ajax_runInstances(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    count = int(request.POST.get('count'))
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")

    logger.info("runInstances: %s, %s, %s, %s"%(
        optionset.profile.name,
        optionset.region.name,
        optionset.name,
        count
    ))

    try:
        instance_ids = run_instances(ec2resource, optionset, count)
    except Exception as ex:
        logger.error("runInstances: %s"%(ex.message))
        return HttpResponse(ex.message, status=500)

    logger.info("runInstances: DONE. %s"%(instance_ids))
    return JSONResponse(instance_ids)


def ajax_addInstanceTags(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    instance_ids = request.POST.getlist('instance_ids[]')
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")

    logger.info("addInstanceTags: %s, %s"%(optionset.name, instance_ids))

    try:
        result = add_instance_tags(ec2resource, optionset, instance_ids)
    except Exception as ex:
        logger.error("addInstanceTags: %s"%(ex.message))
        return HttpResponse(ex.message, status=500)

    logger.info("addInstanceTags: DONE.")
    return JSONResponse(result)


def ajax_addVolumeTags(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    instance_ids = request.POST.getlist('instance_ids[]')
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")

    logger.info("addVolumeTags: %s, %s"%(optionset.name, instance_ids))

    try:
        result = add_volume_tags(ec2resource, instance_ids)
    except Exception as ex:
        logger.error("addVolumeTags: %s"%(ex.message))
        return HttpResponse(ex.message, status=500)

    logger.info("addVolumeTags: DONE.")
    return JSONResponse(result)


def ajax_listInstancesForEC2LaunchOptionSet(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.GET.get('set_id'))
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")
    instances = get_instances_for_ec2launchoptionset(ec2resource, optionset)
    return JSONResponse(instances)


def ajax_startInstance(request):
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    session = boto3.Session(
        profile_name=profile.name,
        region_name=region.code
    )
    instance_id = request.POST.get("instance_id")
    ec2resource = session.resource("ec2")
    instance = ec2resource.Instance(instance_id)

    logger.info("startInstance: %s"%(instance_id))

    try:
        #resp = instance.start(DryRun=True)
        resp = instance.start()
    except Exception as ex:
        logger.error("startInstance: %s"%(ex.message))
        return JSONResponse(ex.message)

    msg = "Instance state: %s --> %s."%(
        resp['StartingInstances'][0]['PreviousState']['Name'],
        resp['StartingInstances'][0]['CurrentState']['Name'],
    )

    logger.info("startInstance: DONE.")
    return JSONResponse(msg)


def ajax_stopInstance(request):
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    session = boto3.Session(
        profile_name=profile.name,
        region_name=region.code
    )
    instance_id = request.POST.get("instance_id")
    ec2resource = session.resource("ec2")
    instance = ec2resource.Instance(instance_id)

    logger.info("stopInstance: %s"%(instance_id))

    try:
        #instance.stop(DryRun=True)
        resp = instance.stop()
    except Exception as ex:
        logger.error("stopInstance: %s"%(ex.message))
        return JSONResponse(ex.message)

    msg = "Instance state: %s --> %s."%(
        resp['StoppingInstances'][0]['PreviousState']['Name'],
        resp['StoppingInstances'][0]['CurrentState']['Name'],
    )

    logger.info("stopInstance: DONE.")
    return JSONResponse(msg)
    


def ajax_terminateInstance(request):
    profile = get_object_or_404(Profile, pk=request.POST.get('profile_id'))
    region = get_object_or_404(Region, pk=request.POST.get('region_id'))
    session = boto3.Session(
        profile_name=profile.name,
        region_name=region.code
    )
    instance_id = request.POST.get("instance_id")
    ec2resource = session.resource("ec2")
    instance = ec2resource.Instance(instance_id)

    logger.info("terminateInstance: %s"%(instance_id))

    try:
        #instance.terminate(DryRun=True)
        resp = instance.terminate()
    except Exception as ex:
        logger.error("terminateInstance: %s"%(ex.message))
        return JSONResponse(ex.message)

    msg = "Instance state: %s --> %s."%(
        resp['TerminatingInstances'][0]['PreviousState']['Name'],
        resp['TerminatingInstances'][0]['CurrentState']['Name'],
    )

    logger.info("terminateInstance: DONE.")
    return JSONResponse(msg)


def ajax_stopAllInstances(request):
    optionset = get_object_or_404(EC2LaunchOptionSet, pk=request.POST.get('set_id'))
    session = boto3.Session(
        profile_name=optionset.profile.name,
        region_name=optionset.region.code
    )
    ec2resource = session.resource("ec2")
    instances = get_instances_for_ec2launchoptionset(ec2resource, optionset)
    instance_ids = []
    for instance in instances:
        if instance['state'] not in ['terminated', 'shutting-down']:
            instance_ids.append(instance['id'])

    logger.info("stopAllInstances: %s"%(instance_ids))

    try:
        ec2client = session.client("ec2")
        resp = ec2client.stop_instances(InstanceIds=instance_ids)
    except Exception as ex:
        logger.error("stopAllInstances: %s"%(ex.message))
        return JSONResponse(ex.message)

    msg = "Instance states: \n "
    for stopping_instance in resp['StoppingInstances']:
        msg += "%s: %s -> %s \n "%(stopping_instance['InstanceId'],
                                   stopping_instance['PreviousState']['Name'],
                                   stopping_instance['CurrentState']['Name'])

    logger.info("stopAllInstances: DONE.")
    return JSONResponse(msg)


def remove_names(request):
    out = ""
    for optionset in EC2LaunchOptionSet.objects.all():
        print(optionset.id)
        obj = json.loads(optionset.content)
        out += str(optionset.id)+": \n<br/>"
        try:
            obj.pop('name')
            out += "Key 'Name' removed.\n<br/>"
        except:
            pass
        try:
            obj['tags'].pop('Name')
            out += "Tag key 'Name' removed.\n<br/>"
        except:
            pass
        optionset.content = json.dumps(obj, indent=2)
        optionset.save()
        out += "\n</br>"
    return HttpResponse(out)


def f1(request):
    def get_list_of(attr, seq):
        return list(map(lambda x:x[attr], seq))

    PROFILE_NAME = "cn-prd"
    REGION_NAME = "cn-north-1"

    session = boto3.Session(profile_name=PROFILE_NAME, region_name=REGION_NAME)
    client = session.client("elb")
    ec2resource = session.resource("ec2")

    optionset = EC2LaunchOptionSet.objects.get(pk=100)
    instances = get_instances_for_ec2launchoptionset(ec2resource, optionset)
    return JSONResponse(instances)