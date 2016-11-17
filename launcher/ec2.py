import json
import re

import boto3


def run_instances(ec2res, optionset, count):
    """Run 'count' number of instances use settings defined in 'optionset'.
    Returns a list of instance ids on success.
    """
    opset = json.loads(optionset.content)
    # check disk settings:
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
    # check security group settings:
    if opset.has_key('security_groups'):
        security_group_ids = [x[1] for x in opset['security_groups']]
    else:
        security_group_ids = [opset['security_group'][1]]
    # try to run instances:
    try:
        instances = ec2res.create_instances(
            BlockDeviceMappings=block_device_mappings,
            IamInstanceProfile={
                'Arn': opset['instance_profile'][1]
            },
            ImageId=opset['image'][1],
            InstanceType=opset['instance_type'],
            KeyName=opset['keypair'][1],
            MinCount=count,
            MaxCount=count,
            SecurityGroupIds=security_group_ids,
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
                'Values': ['running', 'stopped', 'stopping', 'pending']
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
    """Add volume tags with instance information"""
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
            #flag = True
            for volume in instance.volumes.all():
                volume.create_tags(Tags=boto3tags)
                #flag = False
            #if flag:
                # retry...
            ret.update({instance.id: True})
        except Exception as ex:
            ret.update({instance.id: False})
    return ret


def get_instances_for_ec2launchoptionset(ec2res, optionset):
    def name_cmp(x, y):
        """Compare instance names.
        
        For modules with +10 instances, string length needs to be considered, 
        otherwise 'xxx-9' will be greater than 'xxx-10'."""
        len_x = len(x)
        len_y = len(y)
        if len_x < len_y:
            return -1
        if len_x > len_y:
            return 1
        if x < y:
            return -1
        if x > y:
            return 1
        return 0

    ret = []
    prefix = optionset.instance_name_prefix
    # list instances with the same prefix:
    instances = ec2res.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [prefix+"*"]
            },
        ]
    )

    p = prefix+"-(\d+)"
    for instance in instances:
        n = find_name_tag(instance)
        m = re.match(p, n)
        if m is not None:
            ret.append({
                'id': instance.id,
                'name': n,
                'state': instance.state['Name']
            })
            #ret.append(instance)
        ret.sort(cmp=name_cmp, key=lambda l:l['name'])
    return ret