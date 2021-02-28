import abc
from typing import Optional

from protocol.utils import abstractproperty
from protocol.packets.base import PacketBase
from protocol.fields.base import Bytes

from protocol.fields.header import Version, Code, PayloadSize, \
    SenderClientID
from protocol.fields.payload import ClientName, PublicKey
from protocol.fields.message import StaticMessageType, \
    ReceiverClientID, StaticMessageContentSize, \
    EncryptedSymmetricKey, EncryptedMessageContent, \
    EncryptedFileContent


class Request(PacketBase, metaclass=abc.ABCMeta):
    """Abstract class of a request in MessageU protocol."""

    VERSION = 2

    def __init__(self):
        self.payload_size = self.length_of_fields(self.payload_fields)
        self.header_fields = (
            Version(self.VERSION),
            Code(self.CODE),
            PayloadSize(self.payload_size),
            SenderClientID(),
        )


class RegisterRequest(Request):
    """Registration of a new client request.

    Upon sending, expects a RegisterResponse or ErrorResponse from the server.
    """

    CODE = 100

    payload_fields = (
        ClientName(),
        PublicKey(),
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

    payload_fields = (ClientName(), )


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
    MESSAGE_CONTENT_FIELD: Optional[Bytes]

    def __int__(self):
        self.content_size = self.MESSAGE_CONTENT_FIELD.length
        self.payload_fields = (
            ReceiverClientID(),
            StaticMessageType(self.MESSAGE_TYPE),
            StaticMessageContentSize(self.content_size),
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
    MESSAGE_CONTENT_FIELD = EncryptedSymmetricKey()


class SendMessageRequest(PushMessageRequest):
    """Send text message to other client request.

    Upon sending, expects a SendMessageResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 3
    MESSAGE_CONTENT_FIELD = EncryptedMessageContent()


class SendFileRequest(PushMessageRequest):
    """Send file content to other client request.

    Upon sending, expects a SendFileResponse or ErrorResponse from the server.
    """

    MESSAGE_TYPE = 3
    MESSAGE_CONTENT_FIELD = EncryptedFileContent()


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
