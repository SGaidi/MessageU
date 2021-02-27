import abc

from protocol.utils import abstractproperty
from protocol.fields import StaticIntField
from protocol.packetbase import PacketBase


class Request(PacketBase, metaclass=abc.ABCMeta):
    """Abstract class of a request in MessageU protocol."""

    VERSION = 2

    CODE_FIELD = StaticIntField(value=CODE, length=1)

    HEADER_FIELDS = (
        PacketBase.CLIENT_ID_FIELD,
        PacketBase.VERSION_FIELD,
        CODE_FIELD,
        PacketBase.PAYLOAD_SIZE_FIELD,
        PacketBase.MESSAGE_TYPE_FIELD,
    )


class RegisterRequest(Request):
    """Registration of a new client request.

    Upon sending, expects a RegisterResponse or ErrorResponse from the server.
    """

    CODE = 100

    PAYLOAD_FIELDS = (
        PacketBase.NAME_FIELD,
        PacketBase.PUBLIC_KEY_FIELD,
    )


class ListClientsRequest(Request):
    """List all existing clients request.

    Upon sending, expects a ListClientsResponse or ErrorResponse from the
      server.
    """

    CODE = 101

    PAYLOAD_FIELDS = ()


class PublicKeyRequest(Request):
    """Get public-key of a specific client request.

    Upon sending, expects a PublicKeyResponse or ErrorResponse from the server.
    """

    CODE = 102

    PAYLOAD_FIELDS = (PacketBase.CLIENT_ID_FIELD, )


class PushMessageRequest(Request, metaclass=abc.ABCMeta):
    """Push a message to a client request.

    Upon sending, expects a PushMessageResponse or ErrorResponse from the
      server.
    """

    CODE = 103

    @abstractproperty
    def MESSAGE_TYPE(self) -> int: pass

    PAYLOAD_FIELDS = (
        PacketBase.CLIENT_ID_FIELD,
        PacketBase.MESSAGE_TYPE_FIELD,
        PacketBase.CONTENT_SIZE_FIELD,
        PacketBase.MESSAGE_CONTENT_FIELD,
    )


class GetSymmetricKeyRequest(PushMessageRequest):
    """Get symmetric key from other client request.

    Upon sending, expects a GetSymmetricKeyResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 1


class SendSymmetricKeyRequest(PushMessageRequest):
    """Send symmetric key to other client request.

    Upon sending, expects a SendSymmetricKeyResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 2

    PAYLOAD_FIELDS = PushMessageRequest.PAYLOAD_FIELDS + \
                     (PushMessageRequest.ENCRYPTED_SYMMETRIC_KEY_FIELD, )


class SendMessageRequest(PushMessageRequest):
    """Send text message to other client request.

    Upon sending, expects a SendMessageResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 3

    PAYLOAD_FIELDS = PushMessageRequest.PAYLOAD_FIELDS + \
                     (PushMessageRequest.ENCRYPTED_MESSAGE_FIELD,)


class SendFileRequest(PushMessageRequest):
    """Send file content to other client request.

    Upon sending, expects a SendFileResponse or ErrorResponse from the server.
    """

    MESSAGE_TYPE = 3

    PAYLOAD_FIELDS = PushMessageRequest.PAYLOAD_FIELDS + \
                     (PushMessageRequest.ENCRYPTED_FILE_FIELD, )


class PopMessagesRequest(Request):
    """Pop a messages of a client request.

    Upon sending, expects a PopMessagesResponse or ErrorResponse from the
      server.
    """

    CODE = 104

    PAYLOAD_FIELDS = ()


Request.ALL = (
    RegisterRequest, ListClientsRequest, PublicKeyRequest, PushMessageRequest,
    GetSymmetricKeyRequest, SendSymmetricKeyRequest, SendMessageRequest,
    SendFileRequest, PopMessagesRequest,
)
