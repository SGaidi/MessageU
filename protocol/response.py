import abc
from typing import Tuple, Iterable

from protocol.packetbase import PacketBase
from protocol.fields import StaticIntField


class Response(PacketBase, metaclass=abc.ABCMeta):

    VERSION = 2

    CODE_FIELD = StaticIntField(name='code', value=PacketBase.CODE, length=2)

    HEADER_FIELDS = (
        PacketBase.VERSION_FIELD,
        CODE_FIELD,
        PacketBase.PAYLOAD_SIZE_FIELD,
        PacketBase.MESSAGE_ID_FIELD,
    )


class RegisterResponse(Response):

    CODE = 1000

    PAYLOAD_FIELDS = (Response.SENDER_CLIENT_ID_FIELD, )


class ListClientsResponse(Response):

    CODE = 1001

    # TODO: compound field type
    PAYLOAD_FIELDS = (
        Response.SENDER_CLIENT_ID_FIELD,
        Response.NAME_FIELD,
    )

    PAYLOAD_FIELDS_REPEAT = True

    def __init__(self, clients: Iterable[Tuple[int, str]]):
        clients_bytes = b''
        for client_id, client_name in clients:
            client_id_bytes = self.field_to_bytes('client_id', client_id)
            client_name_bytes = self.field_to_bytes('name', client_name)
            clients_bytes += client_id_bytes + client_name_bytes
        super(ListClientsResponse, self).__init__(payload=clients_bytes)


class PublicKeyResponse(Response):

    CODE = 1002

    def __init__(self, client_id: int, public_key: bytes):
        client_id_bytes = self.field_to_bytes('client_id', client_id)
        payload = client_id_bytes + public_key
        super(PublicKeyResponse, self).__init__(payload=payload)


class PushMessageResponse(Response):

    CODE = 1003

    def __init__(self, receiver_client_id: int, message_id: int):
        receiver_client_id_bytes = self.field_to_bytes(
            'client_id', receiver_client_id)
        message_id_bytes = self.field_to_bytes('message_id', message_id)
        payload = receiver_client_id_bytes + message_id_bytes
        super(PushMessageResponse, self).__init__(payload=payload)


class PopMessagesResponse(Response):

    CODE = 1004

    def __init__(self, messages: Iterable[Tuple[int, int, int, bytes]]):
        messages_bytes = b''
        for client_id, message_id, message_type, content in messages:
            client_id_bytes = self.field_to_bytes('client_id', client_id)
            message_id_bytes = self.field_to_bytes('message_id', message_id)
            message_type_bytes = \
                self.field_to_bytes('message_type', message_type)
            message_bytes = client_id_bytes + message_id_bytes + \
                message_type_bytes
            messages_bytes += message_bytes
        super(PopMessagesResponse, self).__init__(payload=messages_bytes)


class ErrorResponse(Response):

    CODE = 9000

    def __init__(self):
        super(ErrorResponse, self).__init__(payload=b'')


Response.ALL = (
    RegisterResponse, ListClientsResponse, PublicKeyResponse,
    PushMessageResponse, PopMessagesResponse, PopMessagesResponse,
    ErrorResponse,
)


__all__ = [cls.__name__ for cls in Response.ALL]
