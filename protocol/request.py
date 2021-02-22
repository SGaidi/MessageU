import abc

from protocol.packetbase import PacketBase


class Request(PacketBase, metaclass=abc.ABCMeta):
    """Abstract class of a request in MessageU protocol."""

    FIELDS_TO_TYPE_AND_LENGTH = dict(PacketBase.FIELDS_TO_TYPE_AND_LENGTH)
    FIELDS_TO_TYPE_AND_LENGTH.update({
        'code': (int, 1),
    })

    VERSION = 2

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
        sender_client_id_bytes = \
            self.field_to_bytes('client_id', sender_client_id)
        extended_payload = sender_client_id_bytes + payload
        super(Request, self).__init__(extended_payload)


class RegisterRequest(Request):
    """Registration of a new client request.

    Upon sending, expects a RegisterResponse or ErrorResponse from the
      server.
    """

    CODE = 100

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
        'message_type': (int, 1),
        'content_size': (int, 4),
    })

    @property
    @abc.abstractmethod
    def MESSAGE_TYPE(self) -> int: pass

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
            self.field_to_bytes('message_content', message_content)
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

    MESSAGE_TYPE = 2

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

    MESSAGE_TYPE = 3

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

    MESSAGE_TYPE = 3

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

    def __init__(self, sender_client_id: int):
        """Initializes request with sender client ID, and passes payload to
          base class.

        Args:
            sender_client_id: Sender client ID.
        """
        super(PopMessagesRequest, self).__init__(
            sender_client_id=sender_client_id)
