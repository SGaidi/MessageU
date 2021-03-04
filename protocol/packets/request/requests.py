from protocol.fields.payload import ClientName, PublicKey, RequestedClientID
from protocol.packets.request.base import Request
from protocol.packets.request.messages import PushMessageRequest


class RegisterRequest(Request):
    """Registration of a new client request.

    Upon sending, expects a RegisterResponse or ErrorResponse from the server.
    """

    CODE = 100

    def __init__(self):
        super(RegisterRequest, self).__init__()
        self._update_header_value('sender_client_id', 0)

    payload_fields = (
        ClientName(),
        PublicKey(),
    )


class ListClientsRequest(Request):
    """List all existing clients request.

    Upon sending, expects a ListClientsResponse or ErrorResponse from the
      server.
    """

    CODE = 101


class PublicKeyRequest(Request):
    """Get public-key of a specific client request.

    Upon sending, expects a PublicKeyResponse or ErrorResponse from the server.
    """

    CODE = 102

    payload_fields = (RequestedClientID(), )


class PopMessagesRequest(Request):
    """Pop a messages of a client request.

    Upon sending, expects a PopMessagesResponse or ErrorResponse from the
      server.
    """

    CODE = 104

    payload_fields = ()


ALL_REQUESTS = (
    RegisterRequest, ListClientsRequest, PublicKeyRequest, PushMessageRequest,
    PopMessagesRequest,
)
