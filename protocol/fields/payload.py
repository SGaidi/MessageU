from protocol.fields.base import String, Compound, Int, ClientID


class ClientName(String):

    LENGTH = 255

    def __init__(self):
        super(ClientName, self).__init__(
            name='client_name', length=self.LENGTH)


class PublicKey(String):

    E_VALUE = 65537  # according to FIPS PUB 186-4

    def __init__(self):
        super(PublicKey, self).__init__(name='public_key', length=271)


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
