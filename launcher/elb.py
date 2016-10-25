import json
import re

import boto3


def get_elb_instance_ids(elbclient, elbname):
    try:
        resp = elbclient.describe_load_balancers(LoadBalancerNames=[elbname])
    except:
        return None
    return list(map(
        lambda x:x['InstanceId'],
        resp['LoadBalancerDescriptions'][0]['Instances']
    ))


def register_instances_with_load_balancer(elbclient, elbname, instance_ids):
    Instances = list(map(
        lambda x: {'InstanceId': x},
        instance_ids
    ))
    try:
        elbclient.register_instances_with_load_balancer(
            LoadBalancerName=elbname,
            Instances=Instances,
            DryRun=True
        )
    except Exception as ex:
        print(ex.message)
    return None

PROFILE_NAME = "cn-prd"
REGION_NAME = "cn-north-1"

def get_list_of(attr, seq):
    return list(map(lambda x:x[attr], seq))

session = boto3.Session(profile_name=PROFILE_NAME, region_name=REGION_NAME)
elbclient = session.client("elb")
ec2resource = session.resource("ec2")

#print(get_elb_instance_ids(elbclient, "prod-elb-connector"))
print(register_instances_with_load_balancer(elbclient, "xxoo", ['i-aaaaaaaa', 'i-bbbbbbbb', 'i-cccccccc']))