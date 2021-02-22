from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from enumchoicefield import EnumChoiceField, ChoiceEnum


class Client(models.Model):

    # TODO: override tables names

    id = models.PositiveIntegerField(
        primary_key=True, help_text="Unique identifier",
        validators=[MinValueValidator(0), MaxValueValidator(2**128 - 1)])
    # Python strings are UTF-8, because ASCII is a subset of UTF-8, it's valid
    name = models.CharField(
        max_length=255, help_text="Client's provided name", unique=True)
    public_key = models.BinaryField(
        max_length=160,
        help_text="Client's provided public-key used in message sending")
    last_seen = models.DateTimeField(
        null=True, blank=True,
        help_text="The last date and time the serverapp received a request "
                  "from the client")


class Message(models.Model):

    class MessageType(ChoiceEnum):
        one = "1"

    id = models.PositiveIntegerField(
        primary_key=True, help_text="Unique identifier",
        validators=[MinValueValidator(0), MaxValueValidator(2 ** 32 - 1)])
    to_client: models.ForeignKey(
        Client, help_text="The message recipient", on_delete=models.CASCADE)
    from_client: models.ForeignKey(
        Client, help_text="The message sender", on_delete=models.CASCADE)
    # did not use `type` name because it's a Python built-in
    message_type = EnumChoiceField(MessageType)  # TOOD:
    content = models.TextField(help_text="The message content")
