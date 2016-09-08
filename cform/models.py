from __future__ import unicode_literals

from django.db import models

FIELD_TYPES = [
    ("string", "string"),
    ("text", "text"),
    ("email", "email address"),
    ("boolean", "boolean"),
    ("number", "number"),
    ("integer", "integer"),
    ("select", "select"),
    ("select_multiple", "multiple select"),
    ("checkbox", "checkbox"),
    ("radio", "radio"),
]

# Create your models here.
class CField(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, default="", blank=True)
    title = models.CharField(max_length=100)
    field_type = models.CharField(max_length=100, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    options = models.TextField(default="", blank=True)

    def __str__(self):
        return self.name


class CFormType(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, default="", blank=True)
    fields = models.ManyToManyField(to=CField)
    field_order = models.CharField(max_length=1000)

    def __str__(self):
        return self.name


class CForm(models.Model):
    name = models.CharField(max_length=100)
    form_type = models.ForeignKey(CFormType, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    


class CFormFieldValue(models.Model):
    form = models.ForeignKey(CForm, on_delete=models.CASCADE)
    field = models.ForeignKey(CField, on_delete=models.CASCADE)
    value = models.CharField(max_length=1000)

    def __str__(self):
        return ": ".join([self.form.name, self.field.name])
