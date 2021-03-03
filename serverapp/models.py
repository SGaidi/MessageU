from django.db import models

from protocol.packets.request import Request


# TODO: add __str__ implementation


class Client(models.Model):

    # TODO: override tables names?

    # Python strings are UTF-8, because ASCII is a subset of UTF-8, it's valid
    name = models.CharField(
        max_length=255, help_text="Client's provided name", unique=True)
    public_key = models.TextField(
        max_length=271,
        help_text="Client's provided public-key used in message sending")
    last_seen = models.DateTimeField(
        null=True, blank=True,
        help_text="The last date and time the server received a request "
                  "from the client")


class Message(models.Model):

    # id = models.PositiveIntegerField(
    #     primary_key=True, help_text="Unique identifier",
    #     validators=[MaxValueValidator(2 ** 32 - 1)])
    to_client = models.ForeignKey(
        Client, related_name='waiting_messages',
        help_text="The message recipient", on_delete=models.CASCADE)
    from_client = models.ForeignKey(
        Client, related_name='sent_messages',
        help_text="The message sender", on_delete=models.CASCADE)
    # did not use `type` name because it's a Python built-in
    message_type = models.PositiveIntegerField(
        choices=[(str(t), t) for t in Request.ALL_MESSAGES_TYPES])
    content = models.TextField(help_text="The message content")
