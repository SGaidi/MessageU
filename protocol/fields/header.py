from protocol.fields.base import StaticInt, ClientID


class Version(StaticInt):

    def __init__(self, version: int):
        super(Version, self).__init__(
            name='version', value=version, length=1,
        )


class Code(StaticInt):

    def __init__(self, code: int):
        super(Code, self).__init__(
            name='code', value=code, length=1,
        )


class PayloadSize(StaticInt):

    def __init__(self, payload_size: int):
        super(PayloadSize, self).__init__(
            name='payload_size', value=payload_size, length=4,
        )


class SenderClientID(ClientID):

    def __init__(self):
        super(SenderClientID, self).__init__(name='sender_client_id')
