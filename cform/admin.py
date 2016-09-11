from django.contrib import admin

from .models import CField, CFormType, CForm, CFormFieldValue

# Register your models here.
class CFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')

admin.site.register(CField, CFieldAdmin)
admin.site.register([CFormType, CForm, CFormFieldValue])
