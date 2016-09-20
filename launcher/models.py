from __future__ import unicode_literals

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
    arn = models.CharField(max_length=500, default=None, blank=True)
    parent = models.ForeignKey('self', 
                                  on_delete=models.CASCADE,
                                  default=None, 
                                  null=True,
                                  blank=True)

    def __str__(self):
        return "['%s', '%s']"%(self.name, self.resource_id)

    def as_option(self):
        return [self.name, self.resource_id]