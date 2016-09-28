import boto3, json, re
from launcher.instancectl import run_instances, find_name_tag, add_instance_tags, add_ebs_tags
from launcher.models import *
del run_instances, find_name_tag, add_instance_tags, add_ebs_tags

s = boto3.Session(profile_name="cn-alpha", region_name="cn-north-1")
r = s.resource("ec2")
opset = EC2LaunchOptionSet.objects.get(pk=125)
o = json.loads(opset.content)

instances = run_instances(r, opset, 2)
add_instance_tags(r, None, opset, iids)

iids = ["i-cccafaf4", "i-cfcafaf7"]