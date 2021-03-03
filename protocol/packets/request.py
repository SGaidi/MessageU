import abc
from typing import Optional

from protocol.packets.base import PacketBase

from protocol.fields.header import Version, RequestCode, PayloadSize, \
    SenderClientID
from protocol.fields.payload import ClientName, PublicKey, RequestedClientID
from protocol.fields.message import MessageType, ReceiverClientID, \
    MessageContentSize, EncryptedSymmetricKey, EncryptedMessageContent, \
    EncryptedFileContent, MessageContent


class Request(PacketBase, metaclass=abc.ABCMeta):
    """Abstract class of a request in MessageU protocol."""

    VERSION = 2

    HEADER_FIELDS_TEMPLATE = (
        Version(VERSION),
        RequestCode(),
        PayloadSize(),
        SenderClientID(),
    )
    
    def __init__(self):
        if self.__class__.__name__ == 'Request':
            # if it's not a concrete request - we don't know the payload
            super(Request, self).__init__(payload_size=None)
        else:
            super(Request, self).__init__()


class RegisterRequest(Request):
    """Registration of a new client request.

    Upon sending, expects a RegisterResponse or ErrorResponse from the server.
    """

    CODE = 100

    def __init__(self):
        super(RegisterRequest, self).__init__()
        self._update_header_value('sender_client_id', 0)

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


class PublicKeyRequest(Request):
    """Get public-key of a specific client request.

    Upon sending, expects a PublicKeyResponse or ErrorResponse from the server.
    """

    CODE = 102

    payload_fields = (RequestedClientID(), )


class PushMessageRequest(Request, metaclass=abc.ABCMeta):
    """Push a message to a client request.

    Upon sending, expects a PushMessageResponse child class or ErrorResponse
      from the server.
    """

    CODE = 103

    MESSAGE_TYPE: int = None
    # TODO: make MessageContentBaseField?
    MESSAGE_CONTENT_FIELD: Optional[MessageContent] = None

    def __init__(self):
        if self.MESSAGE_CONTENT_FIELD is not None:
            self.content_size = self.MESSAGE_CONTENT_FIELD.length
        else:
            self.content_size = float('inf')
        self.payload_fields = (
            ReceiverClientID(),
            MessageType(self.MESSAGE_TYPE),
            MessageContentSize(self.content_size),
        )
        if self.MESSAGE_CONTENT_FIELD is not None:
            print("content field not none")
            self.payload_fields += (self.MESSAGE_CONTENT_FIELD, )
        print(f"c size: {self.content_size}")
        super(PushMessageRequest, self).__init__()


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

    payload_fields = ()


Request.ALL_REQUESTS = (
    RegisterRequest, ListClientsRequest, PublicKeyRequest, PushMessageRequest,
    PopMessagesRequest,
)

Request.ALL_MESSAGES = (
    GetSymmetricKeyRequest, SendSymmetricKeyRequest, SendMessageRequest,
    SendFileRequest,
)

Request.ALL_MESSAGES_TYPES = (message.CODE for message in Request.ALL_MESSAGES)
