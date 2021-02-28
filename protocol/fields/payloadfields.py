from protocol.fields.fieldbase import StringField, BytesField, \
    StaticIntField, CompoundField, IntField


class ClientNameField(StringField):

    def __init__(self):
        super(ClientNameField, self).__init__(
            name='client_name', length=255,
        )


class PublicKeyField(BytesField):

    def __init__(self):
        super(PublicKeyField, self).__init__(
            name='public_key', length=160,
        )


class NoClientIDField(StaticIntField):

    def __init__(self):
        super(NoClientIDField, self).__init__(
            name='no_client_id', value=0, length=16,
        )


class ClientsField(CompoundField):

    def __init__(self):
        super(ClientsField, self).__init__(
            name='clients', fields=(
                IntField(name='client_id', length=16),
                StringField(name='client_name', length=255),
            )
        )


class RequestedClientIDField(IntField):

    def __init__(self):
        super(RequestedClientIDField, self).__init__(
            name='requested_client_id', length=16,
        )
