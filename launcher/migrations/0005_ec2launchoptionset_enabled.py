# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-28 01:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launcher', '0004_ec2launchoptionset'),
    ]

    operations = [
        migrations.AddField(
            model_name='ec2launchoptionset',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
    ]
