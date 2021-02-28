from typing import Union

from protocol.fields.fieldbase import StaticIntField, IntField


class VersionField(StaticIntField):

    def __init__(self, version: int):
        super(VersionField, self).__init__(
            name='version', value=version, length=1,
        )


class CodeField(StaticIntField):

    def __init__(self, code: int):
        super(CodeField, self).__init__(
            name='code', value=code, length=1,
        )


class PayloadSizeField(StaticIntField):

    def __init__(self, payload_size: int):
        super(PayloadSizeField, self).__init__(
            name='payload_size', value=payload_size, length=4,
        )


class SenderClientIDField(IntField):

    def __init__(self):
        super(SenderClientIDField, self).__init__(
            name='sender_client_id', length=16,
        )
