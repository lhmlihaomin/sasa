from django.contrib import admin

from .models import Profile, Region, AWSResource

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_id')

class AWSResourceAdmin(admin.ModelAdmin):
    list_display = ('resource_type', 'name')

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Region)
admin.site.register(AWSResource, AWSResourceAdmin)
