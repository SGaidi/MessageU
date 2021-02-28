from protocol.fields.fieldbase import StaticIntField, IntField, BytesField, \
    UnboundedBytesField, CompoundField
from protocol.fields.headerfields import SenderClientIDField


class ReceiverClientIDField(IntField):

    # TODO: ClientIDFieldBase
    def __init__(self):
        super(ReceiverClientIDField, self).__init__(
            name='receiver_client_id', length=16,
        )


class StaticMessageTypeField(StaticIntField):

    def __init__(self, message_type: int):
        super(MessageTypeField, self).__init__(
            name='message_type', value=message_type, length=1,
        )


class MessageTypeField(IntField):

    def __init__(self):
        super(MessageTypeField, self).__init__(
            name='message_type', length=1,
        )


class StaticMessageContentSizeField(StaticIntField):

    def __init__(self, message_content_size: int):
        super(MessageContentSizeField, self).__init__(
            name='content_size', value=message_content_size, length=4,
        )


class MessageContentSizeField(IntField):

    def __init__(self):
        super(MessageContentSizeField, self).__init__(
            name='content_size', length=4,
        )


class EncryptedSymmetricKeyField(BytesField):

    def __init__(self):
        super(EncryptedSymmetricKeyField, self).__init__(
            name='encrypted_symmetric_key', length=16,
        )


class EncryptedMessageContentField(UnboundedBytesField):

    def __init__(self):
        super(EncryptedMessageContentField, self).__init__(
            name='encrypted_message',
        )


class EncryptedFileContentField(UnboundedBytesField):

    def __init__(self):
        super(EncryptedFileContentField, self).__init__(
            name='encrypted_file',
        )


class MessageIDField(IntField):

    def __init__(self):
        super(MessageIDField, self).__init__(
            name='message_id', length=5,
        )


class MessagesField(CompoundField):

    def __init__(self):
        super(MessagesField, self).__init__(
            name='messages', fields=(
                SenderClientIDField(),
                MessageIDField(),
                MessageTypeField(),
                MessageContentSizeField(),
                UnboundedBytesField(name='message_content'),
            )
        )
