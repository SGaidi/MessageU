import abc

from protocol.packets.base import PacketBase

from protocol.fields.header import Version, Code, \
    PayloadSize
from protocol.fields.payload import NoClientID, Clients, \
    RequestedClientID, PublicKey
from protocol.fields.message import ReceiverClientID, \
    MessageID, Messages


class Response(PacketBase, metaclass=abc.ABCMeta):

    VERSION = 2

    def __init__(self):
        self.payload_size = self.length_of_fields(self.payload_fields)
        self.header_fields = (
            Version(self.VERSION),
            Code(self.CODE),
            PayloadSize(self.payload_size),
        )


class RegisterResponse(Response):

    CODE = 1000

    payload_fields = (NoClientID(), )


class ListClientsResponse(Response):

    CODE = 1001

    payload_fields = (Clients(), )


class PublicKeyResponse(Response):

    CODE = 1002

    payload_fields = (
        RequestedClientID(),
        PublicKey(),
    )


class PushMessageResponse(Response):

    CODE = 1003

    payload_fields = (
        ReceiverClientID(),
        MessageID(),
    )


class PopMessagesResponse(Response):

    CODE = 1004

    payload_fields = (Messages(), )


class ErrorResponse(Response):

    CODE = 9000


Response.ALL = (
    RegisterResponse, ListClientsResponse, PublicKeyResponse,
    PushMessageResponse, PopMessagesResponse, PopMessagesResponse,
    ErrorResponse,
)


__all__ = [cls.__name__ for cls in Response.ALL]
