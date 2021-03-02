from protocol.fields.base import Int, ClientID


# TODO: after logic is done, convert some classes to typing?


class Version(Int):

    def __init__(self, version: int):
        super(Version, self).__init__(name='version', value=version, length=1)


class RequestCode(Int):

    def __init__(self, code: int = None):
        super(RequestCode, self).__init__(name='code', value=code, length=1)


class ResponseCode(Int):

    def __init__(self, code: int = None):
        super(ResponseCode, self).__init__(name='code', value=code, length=2)


class PayloadSize(Int):

    def __init__(self):
        super(PayloadSize, self).__init__(name='payload_size', length=4)


class SenderClientID(ClientID):

    def __init__(self, client_id: int = None):
        super(SenderClientID, self).__init__(
            name='sender_client_id', client_id=client_id,
        )
