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
    def to_dict(obj):
        d = {
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

    @property
    def environ(self):
        if self.profile.name.lower().endswith("prd"):
            return "prd"
        elif self.profile.name.lower.endswith("beta"):
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
        pattern = "([adeprtuv]+)-ami-([a-zA-Z_]+)-([\d\._]+)-([a-zA-Z\d]+)-(\d{8})"
        try:
            content_dict = json.loads(self.content)
            m = re.match(pattern, content_dict['image'][0])
            if m is not None:
                version = m.groups()[2]
                if version == self.version:
                    return True
        except:
            return False
        return False

    @staticmethod
    def to_dict(obj):
        return {
            'id': obj.id,
            'module': obj.module,
            'version': obj.version,
            'region': obj.region.name,
            'az': obj.az,
            'ami_version_match': obj.ami_version_match()
        }