# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-21 06:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launcher', '0002_auto_20160920_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='awsresource',
            name='arn',
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
    ]
