import os
import socket
from typing import Tuple

from mysite import exceptions
from clientapp.clientsideconnection import ClientSideConnection
from protocol.request import Request, RegisterRequest


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
        # TODO: validate host and port format
        # if not (ServerApp.MIN_PORT <= port <= ServerApp.MAX_PORT):
        #     raise exceptions.ServerAppConfigurationError(
        #         f"Invalid port ({port}), "
        #         f"not in range: ({ServerApp.MIN_PORT}, {ServerApp.MAX_PORT})"
        #     )
        return host, port

    def __init__(self):
        self.host, self.port = self._read_server_host_and_port()
        self.connection = ClientSideConnection(self.host, self.port)

    def __send(self, request: Request):
        request_bytes = request.create()

        try:
            self.connection.socket.send(request_bytes)
        except Exception as e:
            raise exceptions.ConnectionException(f"connection: {e}")
        else:
            print("LISTENING")
            res = self.connection.socket.recv(1)
            return res

    def _register(self) -> str:
        if os.path.exists(ClientApp.ME_FILENAME):
            raise exceptions.ClientAppInvalidRequestError(
                f"User is already defined in {ClientApp.ME_FILENAME}.")
        name = input("Enter your name: ")
        public_key = input("Enter your public-key: ").encode().zfill(160)
        # TODO: validate public key
        request = RegisterRequest(name=name, public_key=public_key)
        id = self.__send(request)
        return f"Successfully registered '{name}' " \
               f"with public-key {public_key}. Your ID is {id}."

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
            self._clear_screen()
            print(last_command_output)

            user_input = input(
                f"MessageU client at your service.\n"
                f"1) Register\n"
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
                selected_option, self._wrong_option)
            try:
                last_command_output = action(self)
            except exceptions.ClientAppInvalidRequestError as e:
                last_command_output = str(e)
            except Exception as e:
                last_command_output = f"Server responded with an error: {e}"
