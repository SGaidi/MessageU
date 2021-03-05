from django.db import models

from protocol.fields.payload import ClientName
from protocol.packets.request.messages import PushMessageRequest, \
    ALL_REQUEST_MESSAGES_TYPES


# TODO: add __str__ implementation


class Client(models.Model):

    # TODO: override tables names?
    # TODO: move clients id validation here

    # Python strings are UTF-8, because ASCII is a subset of UTF-8, it's valid
    name = models.CharField(
        max_length=ClientName.LENGTH, unique=True,
        help_text="Client's provided name")
    public_key = models.TextField(
        max_length=271,  # Crypto.RSA PEM certificate length
        help_text="Client's provided public-key used in message sending")
    last_seen = models.DateTimeField(
        null=True, blank=True,
        help_text="The last date and time the server received a request "
                  "from the client")

    def __str__(self):
        return f"Client(name='{self.name}', " \
               f"last_seen={self.last_seen!r})"


class Message(models.Model):

    MessageType = models.IntegerChoices(
        value='MessageType',
        names=[(str(t), t) for t in ALL_REQUEST_MESSAGES_TYPES],
    )

    # TODO: add validator
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
    message_type = models.IntegerField(choices=MessageType.choices)
    content = models.BinaryField(help_text="The message content")
