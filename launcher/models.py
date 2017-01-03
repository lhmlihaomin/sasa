from __future__ import unicode_literals
import json
import re

from django.db import models

# Create your models here.
class Profile(models.Model):
    name = models.CharField(max_length=100)
    account_id = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    profiles = models.ManyToManyField(Profile)

    def __str__(self):
        return self.name

    @staticmethod
    def to_dict(obj):
        return {
            'id': obj.id,
            'name': obj.name,
            'full_name': obj.full_name,
            'code': obj.code
        }


class AWSResource(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, default=None, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, default=None, null=True)
    name = models.CharField(max_length=500)
    resource_id = models.CharField(max_length=500)
    resource_type = models.CharField(max_length=100)
    arn = models.CharField(max_length=500, default=None, blank=True, null=True)
    parent = models.ForeignKey('self', 
                               on_delete=models.CASCADE,
                               default=None, 
                               null=True,
                               blank=True)

    def __str__(self):
        return "['%s', '%s']"%(self.name, self.resource_id)

    def as_option(self):
        return [self.name, self.resource_id]

    @staticmethod
    def get_image_version(image_name):
        pattern = "([adeprtuv]+)-ami-([a-zA-Z_]+)-([\d\._a-zA-Z]+)-([a-zA-Z\d]+)-(\d{8})"
        m = re.match(pattern, image_name)
        if m is not None:
            return m.groups()[2]
        return ""

    @staticmethod
    def filter_image_by_module(profile, region, module_name):
        pattern = "([adeprtuv]+)-ami-%s-([\d\._a-zA-Z]+)-([a-zA-Z\d]+)-(\d{8})"%(module_name,)
        ret = []
        resources = AWSResource.objects.filter(
            profile=profile,
            region=region,
            name__contains=module_name
        )
        for r in resources:
            m = re.match(pattern, r.name)
            if m is not None:
                #version = m.groups()[1]
                #ret.append([r, version])
                ret.append(r)
        return ret

    @staticmethod
    def to_dict(obj):
        d = {
            "id": obj.id,
            "profile": obj.profile.name,
            "region": obj.region.name,
            "name": obj.name,
            "resource_id": obj.resource_id,
            "resource_type": obj.resource_type,
            "arn": obj.arn,
            "parent": "N/A"
        }
        if obj.parent is not None:
            d.update({"parent": obj.parent.name})
        return d


class EC2LaunchOptionSet(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, default=None, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, default=None, null=True)
    module = models.CharField(max_length=500)
    version = models.CharField(max_length=100)
    az = models.CharField(max_length=10)
    content = models.TextField()
    enabled = models.BooleanField(default=True)

    @property
    def environ(self):
        if self.profile.name.lower().endswith("prd"):
            return "prd"
        elif self.profile.name.lower().endswith("beta"):
            return "preprd"
        else:
            return "dev"

    @property
    def name(self):
        return "%s-%s-%s-%s-%s"%(self.environ, 
                                 self.module, 
                                 self.version, 
                                 self.region.name, 
                                 self.az)

    def ami_version_match(self):
        pattern = "([adeprtuv]+)-ami-([a-zA-Z0-9_]+)-([\d\._a-zA-Z]+)-([a-zA-Z\d]+)-(\d{8})"
        print(pattern)
        try:
            content_dict = json.loads(self.content)
            m = re.match(pattern, content_dict['image'][0])
            print(m.groups())
            if m is not None:
                version = m.groups()[2]
                if version == self.version:
                    return True
        except:
            return False
        return False

    @property
    def instance_name_prefix(self):
        if not self.ami_version_match():
            raise Exception("Image")
        return "-".join([self.environ, self.module, self.version, \
            self.region.name, self.az])

    @staticmethod
    def to_dict(obj):
        return {
            'environ': obj.environ,
            'region': obj.region.name,
            'id': obj.id,
            'module': obj.module,
            'version': obj.version,
            'region': obj.region.name,
            'az': obj.az,
            'ami_version_match': obj.ami_version_match(),
            'content': obj.content
        }


class ELB(models.Model):
    name = models.CharField(max_length=1000)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, default=None, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, default=None, null=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.__str__())


TASK_CREATED = 0
TASK_REGISTERED = 1
TASK_INSERVICE = 2
TASK_COMPLETED = 3


class ELBGenericUpdateTask(models.Model):
    elb_name = models.CharField(max_length=1000)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, default=None, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, default=None, null=True)
    instances_reg = models.TextField()
    instances_dereg = models.TextField()
    finished = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    stage = models.IntegerField(default=0)

    def __str__(self):
        return self.elb_name

    def __unicode__(self):
        return unicode(self.__str__())

    def set_stage(self, stage):
        """Set the current stage of this task."""
        # Stages:
        #   0: just created;
        #   1: new instances registered;
        #   2: every new instance "InService"
        #   3: old instances deregistered, task is finished.
        self.stage = stage

    def instances_registered(self):
        self.stage = TASK_REGISTERED

    def instances_inservice(self):
        self.stage = TASK_INSERVICE

    def instances_deregistered(self):
        self.stage = TASK_COMPLETED

    @property
    def status(self):
        progress_txt = ["25%", "50%", "75%", "100%"]
        status_txt = [
            "Task queued.",
            "Registered new instances. Checking health states ...",
            "New instances InService. Deregistering old instances ...",
            "Completed."
        ]
        return (progress_txt[self.stage], status_txt[self.stage])
        