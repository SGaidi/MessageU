from django.contrib import admin

from serverapp.models import Client, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'name', 'public_key', 'last_seen')
    list_display = readonly_fields


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = ('id', 'to_client', 'from_client', 'message_type')
    readonly_fields = list_display + ('content', )
