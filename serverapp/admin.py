from django.contrib import admin

from serverapp.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'name', 'public_key')
    list_display = readonly_fields

