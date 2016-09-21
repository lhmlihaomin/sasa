#!/usr/bin/python
# -*- coding=utf-8 -*-
"""Ec2OptionSet class definition.

This class manages a set of resources/settings which determimes where EC2 
instance(s) will be launched (region, VPC & subnets), the instance(s) specs
(instance type) and configurations (security group, disk size, etc.)

When the "run_instances" method is called, it attempts to launche instances
with these setting values.

Author: lihaomin@tp-link.net

Copyright (C), 2016 , TP-LINK Technologies Co., Ltd.
"""

import json
import sys
import re
import math

import boto.ec2
import boto.ec2.elb
import boto.vpc
import boto.iam

try:
    raw_input
except:
    raw_input = input

class Ec2OptionSet(object):
    """
    A set of options to launch EC2 instances.

    Members:
        num: number of instances to launch;
        image: AMI used to launch instances;
        keypair: SSH kaypair;
        instance_type: instance type;
        vpc: vpc;
        subnets: in which subnets to launch instances. If multiple subnets are 
            selected, instances will be launched across all of them;
        security_group: instance security group;
        alloc_public_ip: boolean. If this instance needs an automatically 
            assigned public IP address;
        tags: dict, tags for these instances;
        instance_profile: instance profile (IAM role) for these instances;

    Methods:
        dummy: (for debugging only) fill object with dummy data;
        show: print formatted object data;
        to_json: convert object data to json format;
        from_json: load object data from a json string;
        run_instances: check options and call boto.ec2.run_instances
    """
    def __init__(self, resources):
        self.name = None
        self.num = 0
        self.image = None
        self.keypair = None
        self.instance_type = None
        self.vpc = None
        self.subnets = []
        self.security_group = None
        self.alloc_public_ip = False
        self.tags = {}
        self.instance_profile = None
        self.resources = resources
        self.use_default_ebs_settings = True
        self.volume_type = "gp2"
        self.volume_size = 0
        self.volume_iops = 0
        self.sourceDestCheck = True

    def _select_from_resources(self, key, items, with_id=True, multiple=False):
        """
        For a list of available options, show a prompt to user and let them 
        select one or more choices from the options.
        Items can be passed in 2 formats: if "with_id" is True, items must be 
        a list of 2-element tuple/lists: [(name1, id1), (name2, id2), ...]; if 
        "with_id" is False, a list of strings.

        Parameters: key (str) - name of the property to be set
                    items (list) - a list of available options
                    with_id (bool) - whether options are simple strings or a 
                                     list of names and ids
                    multiple (bool) - whether multiple options can be selected
        Return type: bool
        Returns:    option (multiple=False) or list of options (multiple=True)
        """
        items.sort()
        input_valid = False
        ret = []
        # loop until input is valid:
        while not input_valid:
            input_valid = True
            # display available items:
            print("SELECT '%s' FROM AVAILABLE ITEMS:"%(key,))
            for index, item in enumerate(items):
                if with_id:
                    print("  %d. %s (%s)"%(index, item[0], item[1]))
                else:
                    print("  %d. %s"%(index, item))
            if multiple:
                prompt = "SELECT AT LEAST ONE ITEM: "
            else:
                prompt = "SELECT AN ITEM: "
            choices = raw_input(prompt)
            # parse input:
            choices = choices.split()
            # input cannot be empty:
            if len(choices) == 0:
                input_valid = False
                continue
            # clear return value:
            ret = []
            # if multiple=True and multiple choices are given, take the 1st one:
            if not multiple:
                choices = [choices[0]]
            # check each choice:
            for choice in choices:
                try:
                    int_choice = int(choice)
                except ValueError:
                    input_valid = False
                    print("INVALID INPUT.")
                    break
                if not 0 <= int_choice < len(items):
                    input_valid = False
                    print("INVALID INPUT.")
                    break
                ret.append(items[int_choice])
        if multiple:
            return ret
        else:
            return ret[0]

    def _get_instance_volumes(self, ec2_conn, instance_id):
        import time
        # retry 5 times before aborting:
        retries = 5
        while retries >= 0:
            volumes = ec2_conn.get_all_volumes(filters={"attachment.instance-id": instance_id})
            if len(volumes) > 0:
                return volumes
            else:
                retries -= 1
                print("Volumes not available. Retry in 5 seconds ...")
                time.sleep(5)
        
    def _add_volume_tags(self, ec2_conn, instance):
        tags = {"InstanceId": instance.id}
        ret = True
        if 'Name' in instance.tags:
            tags.update({'Name': instance.tags['Name']})
        volumes = self._get_instance_volumes(ec2_conn, instance.id)
        print(volumes)
        for volume in volumes:
            print(volume)
            resp = ec2_conn.create_tags(volume.id, tags)
            print(resp)
        return ret

    def dummy(self):
        """fill object with dummy data."""
        self.num = 2
        self.image = ("cloud-standard-20150716", "ami-561c816f")
        self.keypair = "cn-0"
        self.instance_type = "m3.medium"
        self.vpc = ("vpc-prd", "vpc-9bd9cdf9")
        self.subnets = [("sn-prd-prv-a", "subnet-16ddc974"),
                        ("sn-prd-prv-b", "subnet-bf457bcb")]
        self.alloc_public_ip = True
        self.tags = {"Name": "prd-module-1.2.3",
                     "Category": "prd"}
        self.security_group = ("prod-sg-internal-server", "sg-6d0a1c0f")
        return True

    def show(self):
        """display object in a human readable format."""
        print("================= Options ======================")
        sys.stdout.write("1. Number of Instances: ")
        print(self.num)
        print("------------------------------------------------")
        sys.stdout.write("2. Image:\t\t")
        if self.image is None:
            print("None")
        else:
            print("%s (%s)"%(self.image[0], self.image[1]))
        print("------------------------------------------------")
        sys.stdout.write("3. Keyname:\t\t")
        if self.keypair is None:
            print("None")
        else:
            print(self.keypair[0])
        print("------------------------------------------------")
        sys.stdout.write("4. Instance Type:\t")
        if self.instance_type is None:
            print("None")
        else: 
            print(self.instance_type)
        print("------------------------------------------------")
        sys.stdout.write("5. VPC:\t\t\t")
        if self.vpc is None:
            print("None")
        else:
            print("%s (%s)"%(self.vpc[0], self.vpc[1]))
        print("------------------------------------------------")
        sys.stdout.write("6. Subnet(s):\n")
        for subnet in self.subnets:
            print("\t\t\t%s (%s)"%(subnet[0], subnet[1]))
        print("------------------------------------------------")
        sys.stdout.write("7. Public IP: \t\t")
        print(self.alloc_public_ip)
        print("------------------------------------------------")
        sys.stdout.write("8. Tags: \n")
        for key in self.tags:
            print("\t\t\t%s: %s"%(key, self.tags[key]))
        print("------------------------------------------------")
        sys.stdout.write("9. Security Group:\t")
        if self.security_group is None:
            print("None")
        else:
            print("%s (%s)"%(self.security_group[0], self.security_group[1]))
        print("------------------------------------------------")
        sys.stdout.write("10.Instance Profile:\t")
        if self.instance_profile is None:
            print("None")
        else:
            print("%s (%s)"%(self.instance_profile[0], self.instance_profile[1]))
        print("================================================")
        return True

    def to_json(self):
        d = self.__dict__
        d.pop('resources', None)
        return json.dumps(d)

    def from_json(self, txt):
        try:
            d = json.loads(txt)
        except ValueError:
            print("Warning: malformed JSON text. Nothing changed.")
            return False
        props = [
            'subnets',
            'tags',
            'image',
            'instance_type',
            'keypair',
            'num',
            'vpc',
            'security_group',
            'alloca_public_ip'
            ]
        for prop in props:
            if prop in d:
                setattr(self, prop, d[prop])
        return True

    def _input_num(self):
        """input number of instances to launch."""
        self.num = 0
        while self.num <= 0:
            num = raw_input("Input number of instances to run: ")
            try:
                num = int(num)
                if num <= 0:
                    raise Exception("Number must be a positive integer.")
                self.num = num
            except Exception as ex:
                print("Invalid input. Try again.")
        return True

    def _check_params_set(self):
        """check if all requried fields are set."""
        if self.num <= 0:
            raise Exception("num must be a positive integer.")
        if self.image is None:
            raise Exception("image must not be None.")
        if self.keypair is None:
            raise Exception("keypair must not be None.")
        if self.instance_type is None:
            raise Exception("instance type must not be None.")
        if self.vpc is None:
            raise Exception("vpc must not be None.")
        if len(self.subnets) == 0:
            raise Exception("subnet(s) not selected.")
        if len(self.tags) == 0:
            raise Exception("tags not specified.")
        else:
            if 'Name' not in self.tags:
                raise Exception("'Name' tag not found.")
            if 'Category' not in self.tags:
                raise Exception("'Category' tag not found.")
        if self.security_group is None:
            raise Exception("security_group must not be None.")
        return True

    def _check_subnets(self):
        """check if subnet settings are valid."""
        valid_subnets = self.resources['subnets'][self.vpc[1]]
        for subnet_name, subnet_id in self.subnets:
            subnet_found = False
            for valid_subnet in valid_subnets:
                if subnet_id == valid_subnet[1]:
                    subnet_found = True
                    break
            if not subnet_found:
                raise Exception(
                    "Subnet %s (%s) not in VPC %s (%s)"%(
                        subnet_name,
                        subnet_id,
                        self.vpc[0],
                        self.vpc[1]
                    ))
        return True

    def _check_security_group(self):
        valid_groups = self.resources['security_groups'][self.vpc[1]]
        group_found = False
        for valid_group_name, valid_group_id in valid_groups:
            if valid_group_id == self.security_group[1]:
                group_found = True
                break
        if not group_found:
            raise Exception("Security Group %s (%s) not in VPC %s (%s)"%(
                        self.security_group[0],
                        self.security_group[1],
                        self.vpc[0],
                        self.vpc[1]
                    ))
        return True

    def _distribute_subnets(self):
        num_in_each_subnet = {}
        total = int(self.num)
        dec = int(round(float(total) / len(self.subnets)))
        for index, subnet in enumerate(self.subnets):
            if index < len(self.subnets) - 1:
                # put $dec numbers of instances in each subnet ...
                num_in_each_subnet.update({subnet[1]:dec})
                total -= dec
            else:
                # ... except the last one. It gets all the remainder:
                num_in_each_subnet.update({subnet[1]:total})
        return num_in_each_subnet

    def _get_instances_max_number(self, ec2_conn):
        """Get the max instance number whose name starts with self.name"""
        instances = ec2_conn.get_only_instances(filters={"tag:Name":self.name+"*"})
        p = self.name+"-(\d+)"
        max_number = -1
        for instance in instances:
            n = instance.tags['Name']
            m = re.match(p, n)
            if m is not None:
                num = int(m.groups()[0])
                if num > max_number:
                    max_number = num
        return max_number
        

    def run_instances(self, ec2_conn, vpc_conn):
        """Launch EC2 instances with object properties"""
        # get number of instances to launch:
        self._input_num()
        # check property availability:
        print("Checking launch configurations ...")
        ## check if all properties set/valid:
        self._check_params_set()
        ## check if subnets belong to selected VPC:
        self._check_subnets()
        ## check if security group belongs to selected VPC:
        self._check_security_group()
        # calculate instance distribution across subnets:
        num_in_each_subnet = self._distribute_subnets()
        print("Subnet distribution: ")
        print(num_in_each_subnet)
        raw_input()
        # if custom EBS size or IOPS is provided, create volume first:
        if not self.use_default_ebs_settings:
            print("Setting up EBS params ...")
            if self.volume_type == "io1":
                bt = boto.ec2.blockdevicemapping.BlockDeviceType(delete_on_termination=True,
                                                                 size=self.volume_size,
                                                                 volume_type=self.volume_type,
                                                                 iops=self.volume_iops)
            else:
                bt = boto.ec2.blockdevicemapping.BlockDeviceType(delete_on_termination=True,
                                                                 size=self.volume_size,
                                                                 volume_type=self.volume_type)
            bm = boto.ec2.blockdevicemapping.BlockDeviceMapping()
            bm.update({"/dev/sda1": bt})
        else:
            print("Using default EBS settings ...")
            bm = None
        # launch instances in each subnet:
        ##TODO: bugfix: if instances are created across subnets, only the last batch gets tagged.
        instances = []
        for subnet_id in num_in_each_subnet:
            print("Launching instances in subnet %s ..."%(subnet_id,))
            num_in_this_subnet = num_in_each_subnet[subnet_id]
            # get subnet availability zone designation:
            az = vpc_conn.get_all_subnets([subnet_id])[0].availability_zone
            name_suffix = "-" + az[-1]

            print("Launch %d instances in subnet %s"%(num_in_this_subnet, subnet_id))
            try:
                resp = ec2_conn.run_instances(
                    image_id=self.image[1],
                    min_count=num_in_this_subnet,
                    max_count=num_in_this_subnet,
                    key_name=self.keypair[1],
                    security_group_ids=[self.security_group[1]],
                    instance_type=self.instance_type,
                    subnet_id=subnet_id,
                    instance_profile_arn=self.instance_profile[1],
                    block_device_map=bm,
                    #dry_run=True
                    )
                pass
            except Exception as ex:
                print(ex.message)
            print("Instances: "+str(resp.instances))
            instances += resp.instances
        # apply tags to EC2 instance and EBS volumes:
        #if 'Name' not in self.tags:
        #    self.tags.update({'Name': self.name})
        self.tags.update({'Name': self.name})
        max_number = self._get_instances_max_number(ec2_conn)
        num = max_number
        if max_number > 1:
            digits = int(math.ceil(math.log10(max_number)))
        else:
            digits = 1
        for instance in instances:
            num += 1
            fmt = "%s-%0"+str(digits)+"d"
            instance_name = fmt%(self.name, num)
            print("Applying tags to instance %s ..."%(instance.id,))
            instance_tags = self.tags
            instance_tags.update({"Name": instance_name})
            instance.add_tags(instance_tags)
        for instance in instances:
            print("Applying tags to %s's EBS volumes ..."%(instance.id,))
            self._add_volume_tags(ec2_conn, instance)
            # disable Source/Dest. Check if necessary:
            if not self.sourceDestCheck:
                print("Disabling instance Source/Dest. Check ...")
                ec2_conn.modify_instance_attribute(instance.id, "sourceDestCheck", False)
        print("Done.")
        return

    def wizard(self):
        """
        Guide user to set attributes step by step, then perform basic data 
        validation.
        """
        # set "Name" (will be used as tags:Name):
        self.name = raw_input("Input name: ").strip()
        # select AMI:
        print("Select an image:")
        self.image = self._select_from_resources('image', self.resources['images'])
        # select instance type:
        print("Select instance type:")
        self.instance_type = self._select_from_resources('instance_type', self.resources['instance_types'], False)
        # set VPC:
        print("Select a VPC: ")
        self.vpc = self._select_from_resources('vpc', self.resources['vpcs'])
        # select subnets:
        print("Select subnets: ")
        self.subnets = self._select_from_resources('subnet', self.resources['subnets'][self.vpc[1]], True, True)
        # select security group:
        print("Select a security group: ")
        self.security_group = self._select_from_resources('security_group', self.resources['security_groups'][self.vpc[1]])
        # source/dest. check setting (useful for NAT/VPN instances):
        txt = raw_input("DISABLE Source/Dest. check? (y/N)").strip().lower()
        if txt == "y":
            self.sourceDestCheck = False
        # set instance profile:
        print("Select an instance profile:")
        self.instance_profile = self._select_from_resources('instance_profile', self.resources['instance_profiles'])
        # input EBS volume info:
        txt = raw_input("Use default EBS settings? (Y/n) ").strip().lower()
        if txt == "n":
            self.use_default_ebs_settings = False
            self.volume_iops = 0
            self.volume_size = int(raw_input("Input EBS volume size: ").strip())
            self.volume_type = raw_input("Input EBS volume type (standard/io1/gp2): ")
            if self.volume_type not in ('standard', 'io1', 'gp2'):
                self.volume_type = 'standard'
            elif self.volume_type == 'io1':
                self.volume_iops = int(raw_input("Input EBS volume IOPS: ").strip())
        # set key pair:
        print("Select a keypair:")
        self.keypair = self._select_from_resources('keypair', self.resources['keypairs'])
        # read tags:
        print("Input tags: (Format: [key]:[value]. Ends with enter.)")
        lstr = raw_input(">> ").strip()
        while len(lstr) != 0:
            try:
                tag = [i.strip() for i in lstr.split(':')]
                if len(tag) != 2:
                    raise Exception("Format: [key]:[value].")
                key, value = tag
                if len(key)==0 or len(value)==0:
                    raise Exception("Key & value cannot be empty.")
                self.tags.update({key: value})
                print("Tags:\n"+json.dumps(self.tags, indent=2))
            except Exception as ex:
                print(ex.message)
                print("Invalid input. Try again.")
            lstr = raw_input(">> ").strip()
        return True

    def save(self, account, region):
        import copy
        #if self.name is None or self.name == "":
        #    print("Missing EC2 Name. Cannot save.")
        #    return False
        self.tags.update({'Name': self.name})
        fname = ".".join([account.name, region, self.name, "json"])
        d = copy.copy(self.__dict__)
        d.pop('resources', None)
        try:
            fp = open(fname, 'w')
            fp.write(json.dumps(d, indent=2))
            fp.close()
        except:
            print("Failed to save JSON file.")
            return False
        return True

    def load(self, account, region, name):
        fname = ".".join([account.name, region, name, "json"])
        try:
            fp = open(fname, 'r')
            txt = fp.read()
            fp.close()
            d = json.loads(txt)
        except:
            print("Failed to open json file.")
            return False
        props = [
            'name',
            'subnets',
            'tags',
            'image',
            'instance_type',
            'keypair',
            'num',
            'vpc',
            'security_group',
            'alloca_public_ip',
            'instance_profile',
            'use_default_ebs_settings',
            'sourceDestCheck',
            'volume_size',
            'volume_iops',
            ]
        for prop in props:
            if prop in d:
                setattr(self, prop, d[prop])
        return True