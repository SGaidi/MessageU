import abc

from protocol.packets.packetbase import PacketBase

from protocol.fields.headerfields import VersionField, CodeField, \
    PayloadSizeField
from protocol.fields.payloadfields import NoClientIDField, ClientsField, \
    RequestedClientIDField, PublicKeyField
from protocol.fields.messagefields import ReceiverClientIDField, \
    MessageIDField, MessagesField


class Response(PacketBase, metaclass=abc.ABCMeta):

    VERSION = 2

    def __init__(self):
        self.payload_size = self.length_of_fields(self.payload_fields)
        self.header_fields = (
            VersionField(self.VERSION),
            CodeField(self.CODE),
            PayloadSizeField(self.payload_size),
        )


class RegisterResponse(Response):

    CODE = 1000

    payload_fields = (NoClientIDField(), )


class ListClientsResponse(Response):

    CODE = 1001

    payload_fields = (ClientsField(), )


class PublicKeyResponse(Response):

    CODE = 1002

    payload_fields = (
        RequestedClientIDField(),
        PublicKeyField(),
    )


class PushMessageResponse(Response):

    CODE = 1003

    payload_fields = (
        ReceiverClientIDField(),
        MessageIDField(),
    )


class PopMessagesResponse(Response):

    CODE = 1004

    payload_fields = (MessagesField(), )


class ErrorResponse(Response):

    CODE = 9000


Response.ALL = (
    RegisterResponse, ListClientsResponse, PublicKeyResponse,
    PushMessageResponse, PopMessagesResponse, PopMessagesResponse,
    ErrorResponse,
)


__all__ = [cls.__name__ for cls in Response.ALL]
