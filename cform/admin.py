from django.contrib import admin

from .models import CField, CFormType, CForm, CFormFieldValue

# Register your models here.
admin.site.register([CField, CFormType, CForm, CFormFieldValue])