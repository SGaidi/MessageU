from django.contrib import admin

from serverapp.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    readonly_fields = ('name', 'public_key')
