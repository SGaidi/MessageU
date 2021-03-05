from common.utils import FieldsValues
from protocol.fields.payload import Clients, RequestedClientID, PublicKey
from protocol.fields.message import ReceiverClientID, NewClientID, MessageID, \
    Messages
from protocol.packets.response.base import Response


class RegisterResponse(Response):

    CODE = 1000

    payload_fields = (NewClientID(), )


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

    @property
    def compound_length(self) -> int:
        return sum(field.length for field in self.payload_fields[0].fields)

    def pack(self, messages_count: int, **kwargs: FieldsValues) -> bytes:
        self.payload_size = self.compound_length * messages_count
        self._update_header_value('payload_size', self.payload_size)
        return super(PopMessagesResponse, self).pack(**kwargs)


class ErrorResponse(Response):

    CODE = 9000


ALL_RESPONSES = (
    RegisterResponse, ListClientsResponse, PublicKeyResponse,
    PushMessageResponse, PopMessagesResponse, ErrorResponse,
)
