from abc import ABC


class Request(ABC):
    """Abstract data class of a request in MessageU protocol."""

    CLIENT_ID_LENGTH = 16
    VERSION = 2
    VERSION_LENGTH = 1
    CODE_LENGTH = 1
    PAYLOAD_SIZE_LENGTH = 4

    @property
    def CODE(self) -> int:
        raise NotImplementedError(f"Should be implemented in child classes")

    @staticmethod
    def int_to_bytes(param: int, length: int) -> bytes:
        return param.to_bytes(
            length=length,
            byteorder="little",
            signed=False,
        )

    def __init__(self, client_id: int = b'', payload: bytes = b''):
        """
        Args:
            client_id: Client ID field
            code: RequestCode specifying the payload type
            payload: message content in bytes
        """
        self.client_id = Request.int_to_bytes(
            param=client_id, length=Request.CLIENT_ID_LENGTH)
        self.version = Request.int_to_bytes(
            param=Request.VERSION, length=Request.VERSION_LENGTH)
        self.code = Request.int_to_bytes(
            param=self.CODE, length=Request.CODE_LENGTH)
        # TODO: do something with payload
        self.payload = payload
        self.payload_size = self.int_to_bytes(
            param=len(self.payload), length=Request.PAYLOAD_SIZE_LENGTH)

    def __str__(self):
        """Used for debug logging."""
        return "{}(client_id={}, code={}, length={})".format(
            self.__class__.__name__,
            self.client_id,
            self.code,
            len(self.message_id + self.payload),
        )

    def create(self) -> bytes:
        """Returns the entire encoded message in bytes."""
        return self.client_id + self.version + self.code + \
            self.payload_size + self.payload


class RegisterRequest(Request):

    CODE = 100

    NAME_LENGTH = 255
    PUBLIC_KEY_LENGTH = 160

    def __init__(self, name: str, public_key: bytes):
        name_bytes = Request.int_to_bytes(
            param=name, length=RegisterRequest.NAME_LENGTH)
        public_key_bytes = Request.int_to_bytes(
            param=public_key, length=RegisterRequest.PUBLIC_KEY_LENGTH)
        payload = name_bytes + public_key_bytes
        super(RegisterRequest, self).__init__(payload=payload)


class ListClientsRequest(Request):

    CODE = 101

    def __init__(self, sender_client_id: int):
        super(ListClientsRequest, self).__init__(client_id=sender_client_id)


class GetPublicKeyRequest(Request):

    CODE = 102

    def __init__(self, sender_client_id: int, receiver_client_id: int):
        receiver_client_id_bytes = Request.int_to_bytes(
            param=receiver_client_id, length=Request.CLIENT_ID_LENGTH)
        super(ListClientsRequest, self).__init__(
            client_id=sender_client_id, payload=receiver_client_id_bytes)


class PopMessagesRequest(Request):

    CODE = 104

    def __init__(self, sender_client_id: int):
        super(ListClientsRequest, self).__init__(client_id=sender_client_id)


class PushMessageRequest(Request):

    CODE = 103

    MESSAGE_TYPE_LENGTH = 1
    CONTENT_SIZE_LENGTH = 4

    @property
    def MESSAGE_TYPE(self) -> int:
        raise NotImplementedError(f"Should be implemented in child classes")

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            message_content: bytes = b'',
    ):
        receiver_client_id_bytes = Request.int_to_bytes(
            param=receiver_client_id, length=Request.CLIENT_ID_LENGTH)
        message_type_bytes = Request.int_to_bytes(
            param=self.MESSAGE_TYPE, length=PushMessageRequest.MESSAGE_TYPE_LENGTH)
        message_content_size = Request.int_to_bytes(
            param=len(message_content), length=Request.CONTENT_SIZE_LENGTH)
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
