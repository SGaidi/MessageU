from protocol.fields.base import Int, ClientID, UnboundedBytes, \
    BoundedBytes, Compound
from protocol.fields.header import SenderClientID


class ReceiverClientID(ClientID):

    def __init__(self):
        super(ReceiverClientID, self).__init__(name='receiver_client_id')


class MessageType(Int):

    def __init__(self):
        super(MessageType, self).__init__(
            name='message_type', length=1,
        )


class MessageContentSize(Int):

    def __init__(self, message_content_size: int):
        super(MessageContentSize, self).__init__(
            name='content_size', value=message_content_size, length=4,
        )


class MessageContentSize(Int):

    def __init__(self):
        super(MessageContentSize, self).__init__(
            name='content_size', length=4,
        )


class EncryptedSymmetricKey(BoundedBytes):

    def __init__(self):
        super(EncryptedSymmetricKey, self).__init__(
            name='encrypted_symmetric_key', length=16,
        )


class EncryptedMessageContent(UnboundedBytes):

    def __init__(self):
        super(EncryptedMessageContent, self).__init__(
            name='encrypted_message',
        )


class EncryptedFileContent(UnboundedBytes):

    def __init__(self):
        super(EncryptedFileContent, self).__init__(
            name='encrypted_file',
        )


class MessageID(Int):

    def __init__(self):
        super(MessageID, self).__init__(
            name='message_id', length=5,
        )


class Messages(Compound):

    def __init__(self):
        super(Messages, self).__init__(
            name='messages', fields=(
                SenderClientID(),
                MessageID(),
                MessageType(),
                MessageContentSize(),
                UnboundedBytes(name='message_content'),
            )
        )
