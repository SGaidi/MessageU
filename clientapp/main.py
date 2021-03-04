import os
import logging
from typing import Tuple, Type

from common import exceptions
from clientapp.handler import ClientHandler
from protocol.packets.request import PushMessageRequest


logging.getLogger().setLevel(logging.DEBUG)


class ClientApp:

    ME_FILENAME = 'me.info'
    SERVER_FILENAME = 'server.info'

    server_host: str
    server_port: int

    client_name: str = None
    client_id: int = None
    private_key: int = None

    def _read_server_host_and_port(self) -> Tuple[str, int]:
        # TODO: add BASE_URL?
        with open(ClientApp.SERVER_FILENAME) as file:
            try:
                content = file.read()
            except IOError as e:
                raise exceptions.ClientAppEnvironmentException(
                    f"Could not read server info file "
                    f"{ClientApp.SERVER_FILENAME}: {e}")
        try:
            self.server_host, server_port = content.strip().split(':')
            self.server_port = int(server_port)
        except Exception:
            raise exceptions.ServerAppConfigurationError(
                f"Invalid format: {content!s}.")

    def _load_user_info_if_exists(self):
        import base64
        if not os.path.exists(ClientApp.ME_FILENAME):
            return
        with open(ClientApp.ME_FILENAME, 'r') as file:
            try:
                client_name, client_id, private_key_b64 = file
            except Exception as e:
                logging.exception(
                    f"Could not get info from {ClientApp.ME_FILENAME}: {e!r}")
                return
        self.client_name = client_name.strip()
        self.client_id = int(client_id, 16)
        private_key_bytes = base64.b64decode(private_key_b64)
        self.private_key = int.from_bytes(  # noqa # TODO: remove noqa
            bytes=private_key_bytes,
            byteorder="little",
            signed=False,
        )
        print(f"P: {self.private_key}")

    def __init__(self):
        self._read_server_host_and_port()
        self.handler = ClientHandler(self.server_host, self.server_port)
        self._load_user_info_if_exists()

    @property
    def _is_registered(self) -> bool:
        return all([self.client_id, self.client_name, self.private_key])

    def _register(self) -> str:
        import base64
        from Crypto.PublicKey import RSA
        from protocol.packets.request import RegisterRequest

        if os.path.exists(ClientApp.ME_FILENAME):
            # TODO: raise error and exit
            # it was decided not to raise a error so it's easier to use
            #  and debug the app.
            user_input = input(
                f"User info file exist.\n"
                f"Registering will discard the file content.\n"
                f"Do you wish to continue (Y/N)? ")
            if user_input.upper() != 'Y':
                return

        name = input("Enter your name: ")

        key_pair = RSA.generate(1024)
        public_key = key_pair.publickey()
        public_key_pem = public_key.exportKey()
        public_key_string = public_key_pem.decode('ascii')
        print(f"N: {key_pair.d}")
        private_key_bytes = key_pair.d.to_bytes(
            length=128, byteorder='little', signed=False)
        private_key_b64 = base64.b64encode(private_key_bytes).decode()

        request = RegisterRequest()
        fields_to_pack = {'client_name': name, 'public_key': public_key_string}
        response_fields = self.handler.handle(request, fields_to_pack)

        # TODO: rename / refactor different client_id fields
        client_id = response_fields['receiver_client_id']
        with open(ClientApp.ME_FILENAME, 'w+') as file:
            file.write(
                f"{name}\n"
                f"{hex(client_id)}\n"
                f"{private_key_b64!s}\n"
            )

        self.client_name = name
        self.client_id = client_id
        self.private_key = key_pair.d

        return f"Successfully registered '{name}'. " \
               f"Your ID is {client_id}."

    def _list_clients(self) -> str:
        from protocol.packets.request import ListClientsRequest

        request = ListClientsRequest()
        fields_to_pack = {'sender_client_id': self.client_id}
        response_fields = self.handler.handle(request, fields_to_pack)

        clients = response_fields['clients']
        if not clients:
            return 'No clients registered yet.'

        # the response length is validated in Unpacker, so we assume that
        #  len(clients) % 2 == 0, so it can be popped in pairs.
        client_strings = []
        for idx in range(len(clients) // 2):
            client_id = clients[idx * 2]
            client_name = clients[idx * 2 + 1]
            client_strings.append(f'{str(client_id).ljust(10)} {client_name}')
        return '\n'.join(client_strings)

    def _get_public_key_of_client(self, receiver_client_id: int) -> bytes:
        from protocol.packets.request import PublicKeyRequest
        request = PublicKeyRequest()
        request_fields = {
            'requested_client_id': receiver_client_id,
            'sender_client_id': self.client_id,
        }
        response_fields = self.handler.handle(request, request_fields)
        return response_fields['public_key']

    def _pop_messages(self) -> str:
        from protocol.packets.request import PopMessagesRequest
        from protocol.fields.message import Messages

        request = PopMessagesRequest()
        fields_to_pack = {'sender_client_id': self.client_id}
        response_fields = self.handler.handle(request, fields_to_pack)

        messages = response_fields['messages']
        if len(messages) == 0:
            return "You don't have any unread messages."

        messages_strings = []
        print(messages)
        assert len(messages) % len(Messages().fields) == 0
        fields_count = len(Messages().fields)
        for idx in range(len(messages) // fields_count):
            from_client_id = messages[idx * fields_count]
            message_content = messages[idx * fields_count + 4]
            # TODO: keyed messages should display differently
            message_string = \
                f"From: {from_client_id}\n" \
                f"Content:\n" \
                f"{message_content!s}\n" \
                F"-----<EOM>-----"
            messages_strings.append(message_string)
        return '\n'.join(messages_strings)

    def _get_client_id(self) -> int:
        receiver_client_id = input("Enter client id: ")
        try:
            receiver_client_id = int(receiver_client_id)
        except ValueError:
            raise exceptions.ClientValidationError(
                f"Invalid client ID: {receiver_client_id}")
        return receiver_client_id

    def _get_public_key(self) -> str:
        from protocol.packets.request import PublicKeyRequest
        requested_client_id = self._get_client_id()
        request = PublicKeyRequest()
        request_fields = {
            'sender_client_id': self.client_id,
            'requested_client_id': requested_client_id,
        }
        response_fields = self.handler.handle(request, request_fields)
        public_key = response_fields['public_key']
        client_id = response_fields['requested_client_id']
        return f"Client ID: {client_id}\n{public_key!s}"

    def _encrypt_content_with_public_key(
            self, content: str, public_key: bytes,
    ) -> bytes:
        # TODO: encrypt symmetric
        import binascii
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_OAEP
        encryptor = PKCS1_OAEP.new(RSA.importKey(public_key))
        encrypted_content = encryptor.encrypt(content.encode())
        print("Encrypted:", binascii.hexlify(encrypted_content))
        return encrypted_content

    def _send_content(
            self, request_type: Type[PushMessageRequest],
            receiver_client_id: int, content: str = None,
            public_key: bytes = None,
    ) -> str:
        request = request_type()
        request_fields = {
            'receiver_client_id': receiver_client_id,
            'sender_client_id': self.client_id,
        }
        # TODO: change to use symmetric key
        if content and public_key:
            request_fields['content'] = self._encrypt_content_with_public_key(
                content=content, public_key=public_key,
            )
        else:
            request_fields['content'] = b''
        response_fields = self.handler.handle(request, request_fields)
        receiver_client_id = response_fields['receiver_client_id']
        message_id = response_fields['message_id']
        return f"Message {message_id} sent to client with ID " \
               f"{receiver_client_id}."

    def _send_message(self):
        from protocol.packets.request import SendMessageRequest
        receiver_client_id = self._get_client_id()
        # TODO: symmetric key
        public_key = self._get_public_key_of_client(receiver_client_id)
        message = input("Enter message: ")
        return self._send_content(
            request_type=SendMessageRequest,
            receiver_client_id=receiver_client_id,
            content=message,
            public_key=public_key,
        )

    def _send_file(self) -> str:
        from protocol.packets.request import SendFileRequest
        receiver_client_id = self._get_client_id()
        public_key = self._get_public_key_of_client(receiver_client_id)
        pathname = input("Enter pathname: ")
        if not os.path.exists(pathname):
            raise exceptions.ClientAppInvalidRequestError(
                f"No file at: {pathname}")
        with open(pathname, 'r') as file:
            file_content = file.read()
        # TODO: use symmetric key, not public key
        return self._send_content(
            request_type=SendFileRequest,
            receiver_client_id=receiver_client_id,
            content=file_content,
            # public_key=public_key,
        )

    def _get_symmetric_key(self) -> str:
        from protocol.packets.request import GetSymmetricKeyRequest
        receiver_client_id = self._get_client_id()
        return self._send_content(
            request_type=GetSymmetricKeyRequest,
            receiver_client_id=receiver_client_id,
        )

    def _send_symmetric_key(self):
        # from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
        from protocol.packets.request import SendSymmetricKeyRequest
        receiver_client_id = self._get_client_id()
        public_key = self._get_public_key_of_client(receiver_client_id)
        aes_key = get_random_bytes(32)  # for AES-256
        # TODO: use this upon sending messages
        # iv = b''.zfill(16)
        # aes_cbc_key = AES.new(key=key, mode=AES.MODE_CBC)#, iv=iv)
        return self._send_content(
            request_type=SendSymmetricKeyRequest,
            receiver_client_id=receiver_client_id,
            content=aes_key,
            public_key=public_key,
        )

    def _wrong_option(self) -> str:
        return "Wrong option. Please try again."

    OPTION_CODE_TO_ACTION = {
        1: _register,
        2: _list_clients,
        3: _get_public_key,
        4: _pop_messages,
        5: _send_message,
        50: _send_file,
        51: _get_symmetric_key,
        52: _send_symmetric_key,
    }

    def _clear_screen(self):
        from os import name, system
        if name == 'nt':  # Windows
            system('cls')
        elif name == 'posix':  # Mac and Linux
            system('clear')

    def run(self):

        last_command_output = None

        while True:

            # self._clear_screen()
            if last_command_output is not None:
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
            if action.__name__ != '_register' and not self._is_registered:
                last_command_output = "Please register."
            else:
                last_command_output = action(self)


def run():
    client = ClientApp()
    client.run()
