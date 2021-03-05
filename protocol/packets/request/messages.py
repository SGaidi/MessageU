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

    def __init__(self):
        self.payload_fields = (
            ReceiverClientID(),
            MessageType(self.MESSAGE_TYPE),
            MessageContentSize(),
            MessageContent()
        )
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


class SendMessageRequest(PushMessageRequest):
    """Send text message to other client request.

    Upon sending, expects a SendMessageResponse or ErrorResponse from the
      server.
    """

    MESSAGE_TYPE = 3


class SendFileRequest(PushMessageRequest):
    """Send file content to other client request.

    Upon sending, expects a SendFileResponse or ErrorResponse from the server.
    """

    MESSAGE_TYPE = 4


ALL_REQUEST_MESSAGES = (
    GetSymmetricKeyRequest, SendSymmetricKeyRequest, SendMessageRequest,
    SendFileRequest,
)

ALL_REQUEST_MESSAGES_TYPES = \
    (message.MESSAGE_TYPE for message in ALL_REQUEST_MESSAGES)
