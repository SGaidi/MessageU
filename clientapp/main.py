import os
from typing import Tuple

from common import exceptions
from clientapp.handler import ClientHandler
from protocol.packets.request import RegisterRequest


class OtherClient:
    id: int
    public_key: int
    symmetrical_key: int


class ClientApp:

    VERSION = 2
    ME_FILENAME = 'me.info'
    SERVER_FILENAME = 'server.info'

    @staticmethod
    def _read_server_host_and_port() -> Tuple[str, int]:
        # TODO: add BASE_URL
        with open(ClientApp.SERVER_FILENAME) as file:
            try:
                content = file.read()
            except IOError as e:
                raise exceptions.ClientAppEnvironmentException(
                    f"Could not read port file {ClientApp.SERVER_FILENAME}: {e}")
        try:
            host, port = content.strip().split(':')
            port = int(port)
        except ValueError as e:
            raise exceptions.ServerAppConfigurationError(
                f"Invalid port format: {content}. Should be an integer.")
        # TODO: validate host and port format?
        # if not (ServerApp.MIN_PORT <= port <= ServerApp.MAX_PORT):
        #     raise exceptions.ServerAppConfigurationError(
        #         f"Invalid port ({port}), "
        #         f"not in range: ({ServerApp.MIN_PORT}, {ServerApp.MAX_PORT})"
        #     )
        return host, port

    def __init__(self):
        host, port = self._read_server_host_and_port()
        self.handler = ClientHandler(host, port)
        # TODO: load user info if exists

    def _register(self) -> str:
        # TODO: overwrite?
        if os.path.exists(ClientApp.ME_FILENAME):
            raise exceptions.ClientAppInvalidRequestError(
                f"User is already defined in {ClientApp.ME_FILENAME}.")
        name = input("Enter your name: ")
        public_key = input("Enter your public-key: ")
        public_key_bytes = public_key.encode('ascii')
        request = RegisterRequest()
        fields = {'sender_client_id': 0, 'client_name': name, 'public_key': public_key_bytes}
        response_fields = self.handler.handle(request, fields)
        client_id = response_fields['client_id']
        with open(ClientApp.ME_FILENAME, 'w+') as file:
            file.write(
                f"{name}\n"
                f"{hex(client_id)}\n"
                f"{public_key}\n"
            )
        return f"Successfully registered '{name}' " \
               f"with public-key {public_key}. Your ID is {client_id}."

    def _list_clients(self):
        pass

    def _get_public_key(self):
        name = input("Enter client name: ")

        return "public-key"

    def _pop_messages(self):
        try:
            # TODO: get messages
            messages = "blah"
        except:
            pass

        for message in messages:
            other_client_name = message.from_client.name
            # TODO: keys messages should display differently
            print(
                """From: {other_client_name}
                Content:
                {content}
                -----<EOM>-----
                """.format(other_client_name=other_client_name,
                           content=message.content))

    def _push_message(self):
        name = input("Enter client name: ")
        message = input("Enter message: ")
        try:
            pass
            # TODO: send request
        except Exception:
            pass

    def _push_file(self):
        name = input("Enter client name: ")
        pathname = input("Enter pathname: ")
        if not os.path.exists(pathname):
            raise exceptions.ClientAppInvalidRequestError(
                f"No file at: {pathname}")
        try:
            pass
            # TODO: send request
        except Exception:
            pass

    def _request_symmetric_key(self):
        name = input("Enter contact name:")
        try:
            pass
            # TODO: send request
        except Exception:
            pass

    def _respond_with_symmetric_key(self):
        name = input("Enter contact name:")
        # TODO: create symmetric key
        try:
            pass
            # TODO: send request
        except Exception:
            pass

    def _wrong_option(self):
        print(f"Wrong option. Please try again.")

    OPTION_CODE_TO_ACTION = {
        1: _register,
        2: _list_clients,
        3: _get_public_key,
        4: _pop_messages,
        5: _push_message,
        50: _push_file,
        51: _request_symmetric_key,
        52: _respond_with_symmetric_key,
    }

    def _clear_screen(self):
        from os import name, system
        if name == 'nt':  # Windows
            system('cls')
        elif name == 'posix':  # Mac and Linux
            system('clear')

    def run(self):

        last_command_output = ''

        while True:
            # self._clear_screen()
            print(f"*********************************\n"
                  f"{last_command_output}")

            user_input = input(
                f"*********************************\n"
                f"MessageU client at your service.\n"
                f"1) Register\n"
                f"2) Request for clients list\n"
                f"3) Request for public key\n"
                f"4) Request for waiting messages\n"
                f"5) Send a text message\n"
                f"50) Send a file\n"
                f"51) Send a request for symmetric key\n"
                f"52) Send your symmetric key\n"
                f"0) Exit client\n"
                f"? ")
            try:
                selected_option = int(user_input)
            except ValueError:
                selected_option = None

            if selected_option == 0:
                print("Bye!")
                return
            action = ClientApp.OPTION_CODE_TO_ACTION.get(
                selected_option, ClientApp._wrong_option)
            last_command_output = action(self)
            # try:
            #     last_command_output = action(self)
            # except Exception as e:
            #     last_command_output = f"Server responded with an error: {e!r}"


def run():
    client = ClientApp()
    client.run()
