import abc
from typing import Any
from collections import OrderedDict

from protocol.packets.base import PacketBase

from protocol.fields.header import Version, ResponseCode, PayloadSize, SenderClientID
from protocol.fields.payload import Clients, \
    RequestedClientID, PublicKey
from protocol.fields.message import ReceiverClientID, \
    MessageID, Messages


class Response(PacketBase, metaclass=abc.ABCMeta):

    VERSION = 2
    CODE = None

    HEADER_FIELDS_TEMPLATE = (
        Version(VERSION),
        ResponseCode(CODE),
        PayloadSize(),
    )


class RegisterResponse(Response):

    CODE = 1000

    payload_fields = (ReceiverClientID(), )


class ListClientsResponse(Response):

    CODE = 1001

    payload_fields = (Clients(), )

    @property
    def compound_length(self) -> int:
        return sum(field.length for field in self.payload_fields[0].fields)
    
    def pack(self, clients_count: int, **kwargs: OrderedDict[str, Any]) -> bytes:
        self.payload_size = self.compound_length * clients_count
        self._update_header_value('payload_size', self.payload_size)
        return super(ListClientsResponse, self).pack(**kwargs)


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
