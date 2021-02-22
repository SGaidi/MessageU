from abc import ABC

from protocol.base import Base


class Request(Base, ABC):
    """Abstract data class of a request in MessageU protocol."""

    VERSION = 2
    CODE_LENGTH = 1

    def __init__(self, client_id: int = b'', payload: bytes = b''):
        """
        Args:
            client_id: Client ID field
            payload: message content in bytes
        """
        self.client_id = Request.int_to_bytes(
            param=client_id, length=self.CLIENT_ID_LENGTH)
        super(Request, self).__init__(payload)

    def __str__(self):
        """Used for debug logging."""
        return "{}(client_id={}, code={}, length={})".format(
            self.__class__.__name__,
            self.client_id,
            self.code,
            len(self.payload),
        )

    def create(self) -> bytes:
        """Returns the entire encoded message in bytes."""
        return self.client_id + self.version + self.code + \
            self.payload_size + self.payload


class RegisterRequest(Request):

    CODE = 100

    PUBLIC_KEY_LENGTH = 160

    def __init__(self, name: str, public_key: bytes):
        name_bytes = Request.int_to_bytes(
            param=name, length=self.NAME_LENGTH)
        public_key_bytes = Request.int_to_bytes(
            param=public_key, length=self.PUBLIC_KEY_LENGTH)
        payload = name_bytes + public_key_bytes
        super(RegisterRequest, self).__init__(payload=payload)


class ListClientsRequest(Request):

    CODE = 101

    def __init__(self, sender_client_id: int):
        super(ListClientsRequest, self).__init__(client_id=sender_client_id)


class PublicKeyRequest(Request):

    CODE = 102

    def __init__(self, sender_client_id: int, receiver_client_id: int):
        receiver_client_id_bytes = Request.int_to_bytes(
            param=receiver_client_id, length=self.CLIENT_ID_LENGTH)
        super(PublicKeyRequest, self).__init__(
            client_id=sender_client_id, payload=receiver_client_id_bytes)


class PushMessageRequest(Request, ABC):

    CODE = 103

    CONTENT_SIZE_LENGTH = 4

    @property
    def MESSAGE_TYPE(self) -> int:
        raise NotImplementedError(f"Should be defined in child classes.")

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            message_content: bytes = b'',
    ):
        receiver_client_id_bytes = Request.int_to_bytes(
            param=receiver_client_id, length=self.CLIENT_ID_LENGTH)
        message_type_bytes = Request.int_to_bytes(
            param=self.MESSAGE_TYPE, length=self.MESSAGE_TYPE_LENGTH)
        message_content_size = Request.int_to_bytes(
            param=len(message_content), length=self.CONTENT_SIZE_LENGTH)
        payload = receiver_client_id_bytes + message_type_bytes + \
            message_content_size + message_content
        super(PushMessageRequest, self).__init__(
            client_id=sender_client_id, payload=payload)


class GetSymmetricKeyRequest(PushMessageRequest):

    MESSAGE_TYPE = 1

    def __init__(self, sender_client_id: int, receiver_client_id: int):
        super(GetSymmetricKeyRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
        )


class SendSymmetricKeyRequest(PushMessageRequest):

    MESSAGE_TYPE = 2

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            symmetric_key: bytes,
    ):
        super(SendSymmetricKeyRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
            message_content=symmetric_key,
        )


class SendMessageRequest(PushMessageRequest):

    MESSAGE_TYPE = 3

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            message_content: bytes,
    ):
        super(SendSymmetricKeyRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
            message_content=message_content,
        )


class SendFileRequest(PushMessageRequest):

    MESSAGE_TYPE = 3

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            file_content: bytes,
    ):
        super(SendFileRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
            message_content=file_content,
        )


class PopMessagesRequest(Request):

    CODE = 104

    def __init__(self, sender_client_id: int):
        super(PopMessagesRequest, self).__init__(client_id=sender_client_id)
