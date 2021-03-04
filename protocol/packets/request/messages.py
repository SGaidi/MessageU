import abc
from typing import Optional

from protocol.fields.message import EncryptedSymmetricKey, \
    EncryptedMessageContent, EncryptedFileContent, MessageContent, \
    ReceiverClientID, MessageType, MessageContentSize
from protocol.packets.request.base import Request


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

    MESSAGE_TYPE = 4
    MESSAGE_CONTENT_FIELD = EncryptedFileContent()


PushMessageRequest.ALL_MESSAGES = (
    GetSymmetricKeyRequest, SendSymmetricKeyRequest, SendMessageRequest,
    SendFileRequest,
)

PushMessageRequest.ALL_MESSAGES_TYPES = \
    (message.MESSAGE_TYPE for message in PushMessageRequest.ALL_MESSAGES)