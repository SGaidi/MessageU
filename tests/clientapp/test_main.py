import pytest
from typing import Type

from common.exceptions import ClientAppException
from clientapp.main import ClientApp


@pytest.fixture
def client_app(tmp_path) -> Type[ClientApp]:
    ClientApp.SERVER_FILENAME = tmp_path / 'test-server.info'
    ClientApp.ME_FILENAME = tmp_path / 'test-me.info'
    return ClientApp


@pytest.mark.parametrize(
    'file_content,expected_host,expected_port',
    [('127.0.0.1:1234', '127.0.0.1', 1234),
     ('localhost:7538', 'localhost', 7538),
     ('my-domain.org:1600', 'my-domain.org', 1600)]
)
def test_read_server_host_and_port(
        file_content: str, expected_host: str, expected_port: int,
        client_app: Type[ClientApp],
):
    with open(client_app.SERVER_FILENAME, 'w+') as file:
        file.write(file_content)
    client_app._read_server_host_and_port()
    assert client_app.server_host == expected_host
    assert client_app.server_port == expected_port


def test_read_server_host_and_port_file_missing(client_app: Type[ClientApp]):
    with pytest.raises(ClientAppException):
        client_app._read_server_host_and_port()


@pytest.mark.parametrize(
    'file_content',
    ['127.0.0.1:0 1234',
     'local:host:7538',
     'my-domain.org:not a number']
)
def test_read_server_host_and_port_file_invalid(
        file_content: str, client_app: Type[ClientApp]):
    with open(client_app.SERVER_FILENAME, 'w+') as file:
        file.write(file_content)
    with pytest.raises(ClientAppException):
        client_app._read_server_host_and_port()


@pytest.mark.parametrize(
    'file_content,'
    'expected_client_name,expected_client_id,expected_private_key',
    [('username\n'
      '0xf\n'
      'ibyGHo9ez6gZG0jX3XKqREXco3IwQeOd/fnhR2mtUQoBbFlPB98r0wlmJlwF5CjoIoKfvg2'
      'h6LjNKZm+KkuOzQw92VXbH0xBje5JKqkvj2SsY3yeufkSUp3i1Yvdr4wbiOVn93LMaa9/5P'
      'HxtEN6THU2xbvm2/OOEVuHx6MWvB0=',
      'username',
      15,
      int('2088043079284136581867323854783875035157615745365426119573318745983'
          '3298881737636674699143793604836193709591822919756257470359562783053'
          '8608883519235162795368233380161528424666608217154171601193236867305'
          '6178307892239185744162416558074466143576723733122814190234562371888'
          '3063923215803303245203553377829805014153')),
     ('michael\n'
      '0x64f3f63985f04beb81a0e43321880182\n'
      'MIGdMA0GCSqGSIb3DQEB',
      'michael',
      134189521745335319052863344714740924802,
      int('5213685839387135715366813722050864'))]
)
def test_load_user_info_if_exists(
        file_content: str, expected_client_name: str, expected_client_id: int,
        expected_private_key: int, client_app: Type[ClientApp],
):
    with open(client_app.ME_FILENAME, 'w+') as file:
        file.write(file_content)
    client_app._load_user_info_if_exists()
    assert client_app.client_name == expected_client_name
    assert client_app.client_id == expected_client_id
    assert client_app.private_key == expected_private_key


def test_load_user_info_not_exists(client_app: Type[ClientApp]):
    previous_client_name = client_app.client_name
    previous_client_id = client_app.client_id
    previous_private_key = client_app.private_key
    client_app._load_user_info_if_exists()
    assert client_app.client_name == previous_client_name
    assert client_app.client_id == previous_client_id
    assert client_app.private_key == previous_private_key


@pytest.mark.parametrize(
    'file_content',
    ['0xf\n'  # no username
     'ibyGHo9ez6gZG0jX3XKqREXco3IwQeOd/fnhR2mtUQoBbFlPB98r0wlmJlwF5CjoIoKfvg2'
     'h6LjNKZm+KkuOzQw92VXbH0xBje5JKqkvj2SsY3yeufkSUp3i1Yvdr4wbiOVn93LMaa9/5P'
     'HxtEN6THU2xbvm2/OOEVuHx6MWvB0=',
     'username\n'  # no password
     'ibyGHo9ez6gZG0jX3XKqREXco3IwQeOd/fnhR2mtUQoBbFlPB98r0wlmJlwF5CjoIoKfvg2'
     'h6LjNKZm+KkuOzQw92VXbH0xBje5JKqkvj2SsY3yeufkSUp3i1Yvdr4wbiOVn93LMaa9/5P'
     'HxtEN6THU2xbvm2/OOEVuHx6MWvB0=',
     'username\n'  # no public key
     '0xf',
     'valid username\n'  # invalid ID - not in hex format
     'AG\n'
     'ibyGHo9ez6gZG0jX3XKqREXco3IwQeOd/fnhR2mtUQoBbFlPB98r0wlmJlwF5CjoIoKfvg2'
     'h6LjNKZm+KkuOzQw92VXbH0xBje5JKqkvj2SsY3yeufkSUp3i1Yvdr4wbiOVn93LMaa9/5P'
     'HxtEN6THU2xbvm2/OOEVuHx6MWvB0=',
     'valid username\n'  # invalid private key - not a multiple of 4
     '14\n'
     'iby']
)
def test_load_user_info_if_exists_invalid_format(
        file_content: str, client_app: Type[ClientApp],
):
    with open(client_app.ME_FILENAME, 'w+') as file:
        file.write(file_content)
    with pytest.raises(ClientAppException):
        client_app._load_user_info_if_exists()
