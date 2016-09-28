import json
import re

import boto3


def run_instances(ec2res, optionset, count):
    """Run 'count' number of instances use settings defined in 'optionset'.
    Returns a list of instance ids on success.
    """
    # check disk settings:
    opset = json.loads(optionset.content)
    block_device_mappings = []
    if not opset['use_default_ebs_settings'] and opset['volume_type'] == 'io1':
        bdm = {
            #'VirtualName': '',
            'DeviceName': '/dev/sda1',
            'Ebs': {
                #'SnapshotId': '',
                'VolumeSize': opset['volume_size'],
                'DeleteOnTermination': True,
                'VolumeType': opset['volume_type'],
                'Iops': opset['volume_iops'],
                #'Encrypted': False
            },
            #'NoDevice': ''
        }
        block_device_mappings = [bdm]
        # try to run instances:
        try:
            instances = ec2res.create_instances(
                ImageId=opset['image'][1],
                MinCount=count,
                MaxCount=count,
                KeyName=opset['keypair'][1],
                SecurityGroupIds=[opset['security_group'][1]],
                InstanceType=opset['instance_type'],
                BlockDeviceMappings=block_device_mappings,
                SubnetId=opset['subnets'][0][1],
            )
            instance_ids = [x.id for x in instances]
            return instance_ids
        except Exception as ex:
            raise ex

def find_name_tag(instance):
    for tagpair in instance.tags:
        if tagpair['Key'].lower() == 'name':
            return tagpair['Value']
    return ""

def add_instance_tags(ec2res, optionset, instance_ids):
    def get_instances_max_number(prefix, instances):
        p = prefix+"-(\d+)"
        max_number = -1
        for instance in instances:
            n = find_name_tag(instance)
            m = re.match(p, n)
            if m is not None:
                num = int(m.groups()[0])
                if num > max_number:
                    max_number = num
        return max_number
    ret = {}
    prefix = optionset.instance_name_prefix
    # list instances with the same prefix:
    instances = ec2res.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [prefix+"*"]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )
    # get largest instance number:
    max = get_instances_max_number(prefix, instances)
    # tag each instance:
    tags = json.loads(optionset.content)['tags']
    num = max + 1
    for instance_id in instance_ids:
        tags.update({'Name': prefix+"-"+str(num)})
        boto3tags = []
        for key in tags.keys():
            boto3tags.append({
                'Key': key,
                'Value': tags[key]
            })
        num += 1
        
        try:
            instance = ec2res.Instance(instance_id)
            instance.create_tags(
                Tags=boto3tags
            )
            ret.update({instance_id: True})
        except:
            ret.update({instance_id: False})
    return ret


def add_volume_tags(ec2res, instance_ids):
    ret = {}
    # for each instance
    for instance_id in instance_ids:
        try:
            instance = ec2res.Instance(instance_id)
            # get volume tags:
            boto3tags = [{
                'Key': 'InstanceId',
                'Value': instance.id
            },
            {
                'Key': 'Name',
                'Value': find_name_tag(instance)
            }]
            # add tags to volume:
            for volume in instance.volumes.all():
                volume.create_tags(Tags=boto3tags)
            ret.update({instance.id: True})
        except Exception as ex:
            ret.update({instance.id: False})
    return ret