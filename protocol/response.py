import abc
from typing import Tuple, Iterable

from protocol.packetbase import PacketBase


class Response(PacketBase, metaclass=abc.ABCMeta):

    FIELDS_TO_TYPE_AND_LENGTH = dict(PacketBase.FIELDS_TO_TYPE_AND_LENGTH)
    FIELDS_TO_TYPE_AND_LENGTH.update({
        'code': (int, 2),
        'message_id': (int, 4),
    })

    VERSION = 2


class RegisterSuccessfulResponse(Response):

    CODE = 1000

    def __init__(self, new_client_id: int):
        new_client_id_bytes = self.field_to_bytes('client_id', new_client_id)
        super(RegisterSuccessfulResponse, self).__init__(
            payload=new_client_id_bytes)


class ListClientsResponse(Response):

    CODE = 1001

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
