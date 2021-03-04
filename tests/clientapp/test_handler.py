import pytest

from clientapp.handler import ClientHandler
from protocol.fields.message import MessageContent
from protocol.packets.base import PacketBase
from protocol.packets.request.base import Request
from protocol.packets.request.requests import RegisterRequest, \
    ListClientsRequest, PublicKeyRequest, PopMessagesRequest
from protocol.packets.request.messages import GetSymmetricKeyRequest, \
    SendSymmetricKeyRequest, SendMessageRequest, SendFileRequest, \
    PushMessageRequest
from protocol.packets.response import RegisterResponse, \
    ListClientsResponse, PublicKeyResponse, PushMessageResponse, \
    PopMessagesResponse
from protocol.packets.response import Response


@pytest.fixture
def client_handler():
    return ClientHandler('127.0.0.1', 1234)


@pytest.mark.parametrize(
    '_request, expected_response',
    [(RegisterRequest(), RegisterResponse()),
     (ListClientsRequest(), ListClientsResponse()),
     (PublicKeyRequest(), PublicKeyResponse()),
     (PushMessageRequest(), PushMessageResponse()),
     (PopMessagesRequest(), PopMessagesResponse()),
     (GetSymmetricKeyRequest(), PushMessageResponse()),
     (SendSymmetricKeyRequest(), PushMessageResponse()),
     (SendMessageRequest(), PushMessageResponse()),
     (SendFileRequest(), PushMessageResponse())]
)
def test_request_to_response(
        _request: Request, expected_response: Response,
        client_handler: ClientHandler,
):
    response = client_handler._request_to_response(_request)
    assert type(response) == type(expected_response)


@pytest.mark.parametrize(
    '_request',
    [(PacketBase, ),
     (MessageContent(), ),
     (Request, ),
     (RegisterRequest, ),
     (RegisterResponse(), )],
)
def test_request_to_response_fail(
        _request: Request, client_handler: ClientHandler,
):
    with pytest.raises(StopIteration):
        client_handler._request_to_response(_request)


# TODO:
#  1. mock socket (difficult).
#  2. use online server (fixture?). clear db before starting.
#  3. skip.
# @pytest.mark.parametrize(
#     'fields_to_pack',
#     [{'receiver_client_id': 0,
#       'client_name': 'user',
#       'public_key': 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNAD'},
#      {'receiver_client_id': 1,
#       'client_name': 'sarah',
#       'public_key': 'aKTvHi1or/cGr7flcxy7xwqu310Cgvs'}],
# )
# def test_handle_register(
#         fields_to_pack: FieldsValues, client_handler: ClientHandler,
# ):
#     # mock_socket.return_value.send
#     client_handler.handle(RegisterRequest(), fields_to_pack)
#     # mock_socket.send.assert_called_with(('example.com', 12345))
