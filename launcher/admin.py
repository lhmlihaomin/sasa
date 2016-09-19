from django.contrib import admin

from .models import Profile, Region, AWSResource

# Register your models here.
class AWSResourceAdmin(admin.ModelAdmin):
    list_display = ('resource_type', 'name')

admin.site.register([Profile, Region])
admin.site.register(AWSResource, AWSResourceAdmin)
