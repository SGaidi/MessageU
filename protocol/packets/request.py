import abc
from typing import Optional

from protocol.utils import abstractproperty
from protocol.packets.packetbase import PacketBase
from protocol.fields.fieldbase import BytesField

from protocol.fields.headerfields import VersionField, CodeField, \
    PayloadSizeField, SenderClientIDField
from protocol.fields.payloadfields import ClientNameField, PublicKeyField
from protocol.fields.messagefields import StaticMessageTypeField, \
    ReceiverClientIDField, StaticMessageContentSizeField, \
    EncryptedSymmetricKeyField, EncryptedMessageContentField, \
    EncryptedFileContentField


class Request(PacketBase, metaclass=abc.ABCMeta):
    """Abstract class of a request in MessageU protocol."""

    VERSION = 2

    def __init__(self):
        self.payload_size = self.length_of_fields(self.payload_fields)
        self.header_fields = (
            VersionField(self.VERSION),
            CodeField(self.CODE),
            PayloadSizeField(self.payload_size),
            SenderClientIDField(),
        )


class RegisterRequest(Request):
    """Registration of a new client request.

    Upon sending, expects a RegisterResponse or ErrorResponse from the server.
    """

    CODE = 100

    payload_fields = (
        ClientNameField(),
        PublicKeyField(),
    )


class ListClientsRequest(Request):
    """List all existing clients request.

    Upon sending, expects a ListClientsResponse or ErrorResponse from the
      server.
    """

    CODE = 101

    payload_fields = ()


class PublicKeyRequest(Request):
    """Get public-key of a specific client request.

    Upon sending, expects a PublicKeyResponse or ErrorResponse from the server.
    """

    CODE = 102

    payload_fields = (ClientNameField(), )


class PushMessageRequest(Request, metaclass=abc.ABCMeta):
    """Push a message to a client request.

    Upon sending, expects a PushMessageResponse or ErrorResponse from the
      server.
    """

    CODE = 103

    @abstractproperty
    def MESSAGE_TYPE(self) -> int:
        pass

    # TODO: make MessageContentBaseField
    MESSAGE_CONTENT_FIELD: Optional[BytesField]

    def __int__(self):
        self.content_size = self.MESSAGE_CONTENT_FIELD.length
        self.payload_fields = (
            ReceiverClientIDField(),
            StaticMessageTypeField(self.MESSAGE_TYPE),
            StaticMessageContentSizeField(self.content_size),
        )
        if self.MESSAGE_CONTENT_FIELD is not None:
            self.payload_fields += (self.MESSAGE_CONTENT_FIELD, )


class GetSymmetricKeyRequest(PushMessageRequest):
    """Get symmetric key from other client request.

    Upon sending, expects a GetSymmetricKeyResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 1
    MESSAGE_CONTENT_FIELD = None


class SendSymmetricKeyRequest(PushMessageRequest):
    """Send symmetric key to other client request.

    Upon sending, expects a SendSymmetricKeyResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 2
    MESSAGE_CONTENT_FIELD = EncryptedSymmetricKeyField()


class SendMessageRequest(PushMessageRequest):
    """Send text message to other client request.

    Upon sending, expects a SendMessageResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 3
    MESSAGE_CONTENT_FIELD = EncryptedMessageContentField()


class SendFileRequest(PushMessageRequest):
    """Send file content to other client request.

    Upon sending, expects a SendFileResponse or ErrorResponse from the server.
    """

    MESSAGE_TYPE = 3
    MESSAGE_CONTENT_FIELD = EncryptedFileContentField()


class PopMessagesRequest(Request):
    """Pop a messages of a client request.

    Upon sending, expects a PopMessagesResponse or ErrorResponse from the
      server.
    """

    CODE = 104


Request.ALL = (
    RegisterRequest, ListClientsRequest, PublicKeyRequest, PushMessageRequest,
    GetSymmetricKeyRequest, SendSymmetricKeyRequest, SendMessageRequest,
    SendFileRequest, PopMessagesRequest,
)
