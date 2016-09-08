# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-09-08 03:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, default='', max_length=200)),
                ('title', models.CharField(max_length=100)),
                ('field_type', models.CharField(choices=[('string', 'string'), ('text', 'text'), ('email', 'email address'), ('boolean', 'boolean'), ('number', 'number'), ('integer', 'integer'), ('select', 'select'), ('select_multiple', 'multiple select'), ('checkbox', 'checkbox'), ('radio', 'radio')], max_length=100)),
                ('required', models.BooleanField(default=False)),
                ('options', models.TextField(blank=True, default='')),
            ],
        ),
        migrations.CreateModel(
            name='CForm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='CFormFieldValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=1000)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cform.CField')),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cform.CForm')),
            ],
        ),
        migrations.CreateModel(
            name='CFormType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, default='', max_length=200)),
                ('field_order', models.CharField(max_length=1000)),
                ('fields', models.ManyToManyField(to='cform.CField')),
            ],
        ),
        migrations.AddField(
            model_name='cform',
            name='form_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cform.CFormType'),
        ),
    ]
