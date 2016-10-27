import json
import re

import boto3


def get_elbs(elbclient):
    """List load balancer names."""
    try:
        resp = elbclient.describe_load_balancers()
        return list(map(
            lambda x:x['LoadBalancerName'],
            resp['LoadBalancerDescriptions']
        ))
    except Exception as ex:
        print(ex.message)
        return None
    

def get_elb_instance_ids(elbclient, elbname):
    """List instance ids of an ELB."""
    try:
        resp = elbclient.describe_load_balancers(LoadBalancerNames=[elbname])
    except:
        print(ex.message)
        return None
    return list(map(
        lambda x:x['InstanceId'],
        resp['LoadBalancerDescriptions'][0]['Instances']
    ))


def get_elb_instance_states(elbclient, elbname):
    """List instance states of an ELB."""
    ret = {}
    try:
        resp = elbclient.describe_instance_health(LoadBalancerName=elbname)
        for state in resp['InstanceStates']:
            ret.update({state['InstanceId']: state['State']})
        return ret
    except Exception as ex:
        print(ex.message)
        return None

    

def register_elb_instances(elbclient, elbname, instance_ids):
    """Register instances with ELB all at once."""
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
        return False
    return True


def deregister_elb_instances(elbclient, elbname, instance_ids):
    """Deregister instances from elb all at once"""
    Instances = list(map(
        lambda x: {'InstanceId': x},
        instance_ids
    ))
    try:
        elbclient.deregister_instances_from_load_balancer(
            LoadBalancerName=elbname,
            Instances=Instances,
            DryRun=True
        )
    except Exception as ex:
        print(ex.message)
        return False
    return True


PROFILE_NAME = "cn-prd"
REGION_NAME = "cn-north-1"

def get_list_of(attr, seq):
    return list(map(lambda x:x[attr], seq))

session = boto3.Session(profile_name=PROFILE_NAME, region_name=REGION_NAME)
elbclient = session.client("elb")
ec2resource = session.resource("ec2")

#print(get_elb_instance_ids(elbclient, "prod-elb-connector"))
print(register_instances_with_load_balancer(elbclient, "xxoo", ['i-aaaaaaaa', 'i-bbbbbbbb', 'i-cccccccc']))