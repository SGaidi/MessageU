from protocol.fields.base import Int, StaticInt, ClientID


# TODO: after logic si done, convert some classes to typing?


class Version(Int):

    def __init__(self):
        super(Version, self).__init__(name='version', length=1)


class StaticVersion(StaticInt):

    def __init__(self, version: int):
        super(StaticVersion, self).__init__(
            name='version', value=version, length=1,
        )


class RequestCode(Int):

    def __init__(self):
        super(RequestCode, self).__init__(name='code', length=1)


class ResponseCode(Int):

    def __init__(self):
        super(RequestCode, self).__init__(name='code', length=2)


class StaticCode(StaticInt):

    def __init__(self, code: int):
        super(StaticCode, self).__init__(name='code', value=code, length=1)


class PayloadSize(StaticInt):

    def __init__(self, payload_size: int):
        super(PayloadSize, self).__init__(
            name='payload_size', value=payload_size, length=4,
        )


class SenderClientID(ClientID):

    def __init__(self):
        super(SenderClientID, self).__init__(name='sender_client_id')
