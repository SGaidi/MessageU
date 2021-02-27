import abc

from protocol.fields import StaticIntField
from protocol.packetbase import PacketBase


class Request(PacketBase, metaclass=abc.ABCMeta):
    """Abstract class of a request in MessageU protocol."""

    VERSION = 2

    CODE_FIELD = StaticIntField(value=CODE, length=1)

    # 'version': (int, 1),
    # 'payload_size': (int, PAYLOAD_SIZE_LENGTH),
    # 'name': (str, 255),
    # 'public_key': (bytes, 160),  # TODO: add encoding validator
    # 'message_type': (int, 1),

    HEADER_FIELDS = (
        PacketBase.CLIENT_ID_FIELD,
        PacketBase.VERSION_FIELD,
        CODE_FIELD,
        PacketBase.PAYLOAD_SIZE_FIELD,
    )

    def __init__(self, sender_client_id: int = 0, payload: bytes = b''):
        """
        Initializes request with sender client ID and passes payload to base
          class.

        Args:
            sender_client_id: Sender client ID. Could be 0 in case of
              RegisterRequest.
            payload: The rest of the request payload. Could be empty in case of
              ListRequest.
        """
        self.sender_client_id_bytes = \
            self.field_to_bytes('client_id', sender_client_id)
        super(Request, self).__init__(payload)

    def pack(self) -> bytes:
        """Returns the encoded request in bytes."""
        return self.sender_client_id_bytes + super(Request, self).pack()


class RegisterRequest(Request):
    """Registration of a new client request.

    Upon sending, expects a RegisterResponse or ErrorResponse from the
      server.
    """

    CODE = 100

    PAYLOAD_FIELDS = ('name', 'public_key')

    def __init__(self, name: str, public_key: bytes):
        """Initializes request with sender's name and public-key, and passes
          payload to base class.

        Args:
            name: Sender client name.
            public_key: RSA 1024 bit public-key with optional header.
        """
        name_bytes = self.field_to_bytes('name', name)
        public_key = self.field_to_bytes('public_key', public_key)
        payload = name_bytes + public_key
        super(RegisterRequest, self).__init__(payload=payload)


class ListClientsRequest(Request):
    """List all existing clients request.

    Upon sending, expects a ListClientsResponse or ErrorResponse from the
      server.
    """

    CODE = 101

    PAYLOAD_FIELDS = ()

    def __init__(self, sender_client_id: int):
        """Passes payload to base class.

        Args:
            sender_client_id: Sender client ID.
        """
        super(ListClientsRequest, self).__init__(
            sender_client_id=sender_client_id)


class PublicKeyRequest(Request):
    """Get public-key of a specific client request.

    Upon sending, expects a PublicKeyResponse or ErrorResponse from the
      server.
    """

    CODE = 102

    PAYLOAD_FIELDS = ('client_id', )

    def __init__(self, sender_client_id: int, requested_client_id: int):
        """Initializes request with requested client ID, and passes payload to
          base class.

        Args:
            sender_client_id: Sender client ID.
            requested_client_id: Requested client ID.
        """
        requested_client_id_bytes = \
            self.field_to_bytes('client_id', requested_client_id)
        super(PublicKeyRequest, self).__init__(
            sender_client_id=sender_client_id,
            payload=requested_client_id_bytes,
        )


class PushMessageRequest(Request, metaclass=abc.ABCMeta):
    """Push a message to a client request.

    Upon sending, expects a PushMessageResponse or ErrorResponse from the
      server.
    """

    CODE = 103

    FIELDS_TO_TYPE_AND_LENGTH = dict(Request.FIELDS_TO_TYPE_AND_LENGTH)
    FIELDS_TO_TYPE_AND_LENGTH.update({
        'content_size': (int, 4),
    })

    @property
    @abc.abstractmethod
    def MESSAGE_TYPE(self) -> int: pass

    PAYLOAD_FIELDS = ('client_id', 'message_type', 'content_size')

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            message_content: bytes = b'',
    ):
        """Initializes request with receiver client ID, message type, and
          content size; and passes payload to base class.

        Args:
            sender_client_id: Sender client ID.
            receiver_client_id: Receiver client ID.
            message_content: Content to be sent from sender client to receiver
              client. It is encrypted by either a symmetric key or public key,
              depending on the child request.
        """
        receiver_client_id_bytes = \
            self.field_to_bytes('client_id', receiver_client_id)
        message_type_bytes = \
            self.field_to_bytes('message_type', self.MESSAGE_TYPE)
        message_content_size = \
            self.field_to_bytes('content_size', len(message_content))
        payload = receiver_client_id_bytes + message_type_bytes + \
            message_content_size + message_content
        super(PushMessageRequest, self).__init__(
            sender_client_id=sender_client_id, payload=payload)


class GetSymmetricKeyRequest(PushMessageRequest):
    """Get symmetric key from other client request.

    Upon sending, expects a GetSymmetricKeyResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 1

    def __init__(self, sender_client_id: int, receiver_client_id: int):
        """Passes client IDs to base class, no message content.

        Args:
            sender_client_id: Sender client ID.
            receiver_client_id: Receiver client ID.
        """
        super(GetSymmetricKeyRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
        )


class SendSymmetricKeyRequest(PushMessageRequest):
    """Send symmetric key to other client request.

    Upon sending, expects a SendSymmetricKeyResponse or ErrorResponse from the
      server.
    """

    FIELDS_TO_TYPE_AND_LENGTH = dict(PushMessageRequest.FIELDS_TO_TYPE_AND_LENGTH)
    FIELDS_TO_TYPE_AND_LENGTH.update({
        'encrypted_symmetric_key': (bytes, 16),
    })

    MESSAGE_TYPE = 2

    PAYLOAD_FIELDS = PushMessageRequest.PAYLOAD_FIELDS + \
                     ('encrypted_symmetric_key', )

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            symmetric_key: bytes,
    ):
        """Passes client IDs to base class, the message content is the
          encryption of a symmetric key.

        Args:
            sender_client_id: Sender client ID.
            receiver_client_id: Receiver client ID.
            symmetric_key: Symmetric key encrypted with the receiver's
              public-key.
        """
        super(SendSymmetricKeyRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
            message_content=symmetric_key,
        )


class SendMessageRequest(PushMessageRequest):
    """Send text message to other client request.

    Upon sending, expects a SendMessageResponse or ErrorResponse from the
      server.
    """

    FIELDS_TO_TYPE_AND_LENGTH = dict(
        PushMessageRequest.FIELDS_TO_TYPE_AND_LENGTH)
    FIELDS_TO_TYPE_AND_LENGTH.update({
        'encrypted_message': (bytes, float('inf')),
    })

    MESSAGE_TYPE = 3

    PAYLOAD_FIELDS = PushMessageRequest.PAYLOAD_FIELDS + ('encrypted_message',)

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            message_content: bytes,
    ):
        """Passes client IDs to base class, the message content is the
          encryption of text composed by the sender client.

        Args:
            sender_client_id: Sender client ID.
            receiver_client_id: Receiver client ID.
            message_content: Text message encrypted with the symmetric key.
        """
        super(SendSymmetricKeyRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
            message_content=message_content,
        )


class SendFileRequest(PushMessageRequest):
    """Send file content to other client request.

    Upon sending, expects a SendFileResponse or ErrorResponse from the
      server.
    """

    FIELDS_TO_TYPE_AND_LENGTH = dict(
        PushMessageRequest.FIELDS_TO_TYPE_AND_LENGTH)
    FIELDS_TO_TYPE_AND_LENGTH.update({
        'encrypted_file': (bytes, float('inf')),
    })

    MESSAGE_TYPE = 3

    PAYLOAD_FIELDS = PushMessageRequest.PAYLOAD_FIELDS + ('encrypted_file',)

    def __init__(
            self, sender_client_id: int, receiver_client_id: int,
            file_content: bytes,
    ):
        """Passes client IDs to base class, the message content is the
          encryption of file content chosen by the sender client.

        Args:
            sender_client_id: Sender client ID.
            receiver_client_id: Receiver client ID.
            file_content: File content encrypted with the symmetric key.
        """
        super(SendFileRequest, self).__init__(
            sender_client_id=sender_client_id,
            receiver_client_id=receiver_client_id,
            message_content=file_content,
        )


class PopMessagesRequest(Request):
    """Pop a messages of a client request.

    Upon sending, expects a PopMessagesResponse or ErrorResponse from the
      server.
    """

    CODE = 104

    PAYLOAD_FIELDS = ()

    def __init__(self, sender_client_id: int):
        """Initializes request with sender client ID, and passes payload to
          base class.

        Args:
            sender_client_id: Sender client ID.
        """
        super(PopMessagesRequest, self).__init__(
            sender_client_id=sender_client_id)


Request.ALL = (
    RegisterRequest, ListClientsRequest, PublicKeyRequest, PushMessageRequest,
    GetSymmetricKeyRequest, SendSymmetricKeyRequest, SendMessageRequest,
    SendFileRequest, PopMessagesRequest,
)
