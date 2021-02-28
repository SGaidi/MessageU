from protocol.fields.base import String, StaticInt, Compound, Int, \
    BoundedBytes, ClientID


class ClientName(String):

    def __init__(self):
        super(ClientName, self).__init__(
            name='client_name', length=255,
        )


class PublicKey(BoundedBytes):

    def __init__(self):
        super(PublicKey, self).__init__(
            name='public_key', length=160,
        )

    def _validate_encoding(self, field_value: bytes) -> None:
        import base64
        try:
            base64.b64encode(base64.b64decode(field_value)) == field_value
        except Exception as e:
            raise ValueError(f"Invalid encoding: {e!r}")


class NoClientID(StaticInt):

    def __init__(self):
        super(NoClientID, self).__init__(
            name='no_client_id', value=0, length=16,
        )


class Clients(Compound):

    def __init__(self):
        super(Clients, self).__init__(
            name='clients', fields=(
                Int(name='client_id', length=16),
                String(name='client_name', length=255),
            )
        )


class RequestedClientID(ClientID):

    def __init__(self):
        super(RequestedClientID, self).__init__(name='requested_client_id')
