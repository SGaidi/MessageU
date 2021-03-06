from typing import Iterator

from protocol.fields.base import Int, ClientID, UnboundedBytes, \
    BoundedMixin, Compound, Bytes, BoundedBytes
from protocol.fields.header import SenderClientID


class NewClientID(ClientID):
    
    def __init__(self):
        super(NewClientID, self).__init__(name='new_client_id')


class ReceiverClientID(ClientID):

    def __init__(self):
        super(ReceiverClientID, self).__init__(name='receiver_client_id')


class MessageType(Int):

    def __init__(self, message_type: int = None):
        super(MessageType, self).__init__(
            name='message_type', value=message_type, length=1,
        )


class MessageContentSize(Int):

    def __init__(self, content_size: int = float('inf')):
        super(MessageContentSize, self).__init__(
            name='content_size', value=content_size, length=4,
        )


class MessageContent(BoundedBytes):

    def __init__(self, content: bytes = None, length: int = float('inf')):
        super(MessageContent, self).__init__(
            name='content', value=content, length=length)


class MessageID(Int):

    def __init__(self):
        super(MessageID, self).__init__(name='message_id', length=5)


class Messages(Compound):

    def __init__(self):
        super(Messages, self).__init__(
            name='messages', fields=(
                SenderClientID(),
                MessageID(),
                MessageType(),
                MessageContentSize(),
                MessageContent(),
            )
        )
