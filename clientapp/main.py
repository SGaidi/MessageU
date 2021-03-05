import os
import logging
from dataclasses import dataclass, field
from typing import Tuple, Type, Optional, Dict

from Crypto.Cipher import AES

from common.exceptions import ClientAppException, ClientValidationError
from clientapp.handler import ClientHandler
from protocol.packets.request.messages import PushMessageRequest


logging.getLogger().setLevel(logging.DEBUG)


@dataclass
class ClientApp:

    ME_FILENAME = 'me.info'
    SERVER_FILENAME = 'server.info'
    AES_256_BLOCK_BYTES = 16
    AES_256_KEY_BYTES = 32
    AES_IV = b''.zfill(AES_256_BLOCK_BYTES)

    server_host: str
    server_port: int

    client_ids_to_public_keys: Dict[int, bytes]
    client_ids_to_symmetric_keys: Dict[int, Type[AES.new]]

    client_name: Optional[str] = None
    client_id: Optional[int] = None
    private_key: Optional[int] = None

    logger = logging.getLogger(__name__)

    @classmethod
    def _read_server_host_and_port(cls) -> None:
        """Tries reading the host and port from SERVER_FILENAME.
        If fails, raises a ClientAppException."""
        try:
            with open(ClientApp.SERVER_FILENAME, 'r') as file:
                content = file.read()
        except IOError as e:
            raise ClientAppException(
                f"Could not read server info file "
                f"{ClientApp.SERVER_FILENAME}: {e}.")

        try:
            cls.server_host, server_port = content.strip().split(':')
            cls.server_port = int(server_port)
        except Exception:
            raise ClientAppException(f"Invalid format: {content!s}.")

    @classmethod
    def _load_user_info_if_exists(cls):
        """Tries loading local user info.
        If fails to read it, returns.
        If fails to extract information, raises an error. Because it's assumed
          the file is written to by the client app."""
        import base64
        from protocol.fields.base import ClientID

        if not os.path.exists(ClientApp.ME_FILENAME):
            return

        with open(ClientApp.ME_FILENAME, 'r') as file:
            try:
                client_name, client_id, private_key_b64 = file
                cls.client_name = client_name.strip()
                cls.client_id = int(client_id, ClientID.LENGTH)
                private_key_bytes = base64.b64decode(private_key_b64)
                cls.private_key = int.from_bytes(
                    bytes=private_key_bytes,
                    byteorder="little",
                    signed=False,
                )
            except Exception:
                raise ClientAppException(
                    f"Wrong format of {ClientApp.ME_FILENAME}! "
                    f"File corrupted.")

    def __init__(self):
        self._read_server_host_and_port()
        self._load_user_info_if_exists()
        self.handler = ClientHandler(self.server_host, self.server_port)
        self.client_ids_to_public_keys = {}
        self.client_ids_to_symmetric_keys = {}

    @property
    def _is_registered(self) -> bool:
        """Assumes this information is correct."""
        return all([self.client_id, self.client_name, self.private_key])

    def _generate_key_pair(self) -> Tuple[str, str, int]:
        """Generates RSA key pair with length=1024, and e=65537 (default).

        Returns a tuple of:
          Public key PEM certificate, easy to export, import and store in db.
          Private key b64 encoded, so be kept in ME_FILENAME.
          Private key int value, loaded in memory for ease of use."""
        import base64
        from Crypto.PublicKey import RSA

        key_pair = RSA.generate(1024)
        public_key = key_pair.publickey()
        public_key_string = public_key.exportKey().decode('ascii')
        private_key_bytes = key_pair.d.to_bytes(
            length=128, byteorder='little', signed=False)
        private_key_b64_string = base64.b64encode(private_key_bytes).decode()

        return public_key_string, private_key_b64_string, key_pair.d

    def _register(self) -> str:
        from protocol.packets.request.requests import RegisterRequest

        if os.path.exists(ClientApp.ME_FILENAME):
            # TODO: raise error and exit
            # it was decided not to raise a error so it's easier to use
            #  and debug the app.
            user_input = input(
                f"User info file exist.\n"
                f"Registering will discard the file content.\n"
                f"Do you wish to continue (Y/N)? ")
            if user_input.upper() != 'Y':
                return "OK. Nothing changed."

        name = input("Enter your name: ")
        public_key, private_key_str, private_key_int = \
            self._generate_key_pair()

        request = RegisterRequest()
        fields_to_pack = {'client_name': name, 'public_key': public_key}
        response_fields = self.handler.handle(request, fields_to_pack)

        client_id = response_fields['new_client_id']
        with open(ClientApp.ME_FILENAME, 'w+') as file:
            file.write(
                f"{name}\n"
                f"{hex(client_id)}\n"
                f"{private_key_str}\n"
            )

        self.client_name = name
        self.client_id = client_id
        self.private_key = private_key_int

        return f"Successfully registered '{name}'. " \
               f"Your ID is {client_id}."

    def _list_clients(self) -> str:
        """Sends a request for registered clients.
        Formats the returned clients response in a table."""
        from protocol.fields.payload import Clients
        from protocol.packets.request.requests import ListClientsRequest

        request = ListClientsRequest()
        fields_to_pack = {'sender_client_id': self.client_id}
        response_fields = self.handler.handle(request, fields_to_pack)

        clients = response_fields['clients']
        if not clients:
            return 'No clients registered yet.'

        # the response length is validated in Packer/Unpacker, so we expect
        #  that len(clients) % fields_count == 0, so it can be popped
        #  accordingly.
        fields_count = len(Clients().fields)
        assert len(clients) % fields_count == 0
        client_strings = []
        for idx in range(len(clients) // fields_count):
            client_id = clients[idx * fields_count]
            client_name = clients[idx * fields_count + 1]
            client_strings.append(f'{str(client_id).ljust(10)} {client_name}')
        return '\n'.join(client_strings)

    def _get_public_key_of_client(self, requested_client_id: int) -> bytes:
        """If a public key is not saved locally for the requested client,
          sends a request for public key, and saves a public key PEM
          certificate in bytes."""
        from protocol.packets.request.requests import PublicKeyRequest

        if requested_client_id not in self.client_ids_to_public_keys:
            request = PublicKeyRequest()
            request_fields = {
                'requested_client_id': requested_client_id,
                'sender_client_id': self.client_id,
            }
            response_fields = self.handler.handle(request, request_fields)
            self.client_ids_to_public_keys[requested_client_id] = \
                response_fields['public_key']

        return self.client_ids_to_public_keys[requested_client_id]

    def _get_client_id(self) -> int:
        """Prompt user for receiver client ID, and returns it's int value."""
        receiver_client_id = input("Enter client id: ")
        try:
            receiver_client_id = int(receiver_client_id)
        except ValueError:
            raise ClientValidationError(
                f"Invalid client ID: {receiver_client_id}.")
        return receiver_client_id

    def _get_public_key(self) -> str:
        """Prompts user for client ID, requests the public key, and returns
          string description."""
        requested_client_id = self._get_client_id()
        public_key = self._get_public_key_of_client(requested_client_id)
        return f"Client ID: {requested_client_id}\n{public_key!s}"

    def _encrypt_symmetric_key_with_public_key(
            self, symmetric_key: bytes, public_key: bytes,
    ) -> bytes:
        """Import PEM certificate public key bytes, and use it to encrypt
        content."""
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_OAEP

        encryptor = PKCS1_OAEP.new(RSA.importKey(public_key))
        return encryptor.encrypt(symmetric_key)

    def _decrypt_symmetric_key_with_private_key(
            self, encrypted_symmetric_key: bytes, public_key_pem: str,
    ) -> Type[AES.new]:
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_OAEP
        from protocol.fields.payload import PublicKey

        public_key_obj = RSA.importKey(public_key_pem)
        key_pair = RSA.construct(
            (public_key_obj.n, PublicKey.E_VALUE, self.private_key))
        decrypter = PKCS1_OAEP.new(key_pair)
        symmetric_key = decrypter.decrypt(encrypted_symmetric_key)

        return AES.new(
            key=symmetric_key,
            iv=ClientApp.AES_IV,
            mode=AES.MODE_CBC,
        )

    def _load_symmetric_key(self, requested_client_id: int) -> Type[AES.new]:
        try:
            return self.client_ids_to_symmetric_keys[requested_client_id]
        except KeyError:
            raise ClientAppException(
                f"Did not yet receive the symmetric key from client with ID "
                f"{requested_client_id}.")

    def _encrypt_with_symmetric_key(
            self, content: bytes, requested_client_id: int,
    ) -> bytes:
        # TODO: padding
        # https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
        from common.utils import islice

        aes_cbc_key = self._load_symmetric_key(requested_client_id)
        encrypted_blocks = []
        for block in islice(content, ClientApp.AES_256_BLOCK_BYTES):
            encrypted_block = aes_cbc_key.encrypt(block)
            encrypted_blocks.append(encrypted_block)

        return b''.join(encrypted_blocks)

    def _decrypt_with_symmetric_key(
            self, content: bytes, requested_client_id: int,
    ) -> bytes:
        # TODO: padding
        # https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
        from common.utils import islice

        aes_cbc_key = self._load_symmetric_key(requested_client_id)
        decrypted_blocks = []
        for block in islice(content, ClientApp.AES_256_BLOCK_BYTES):
            decrypted_block = aes_cbc_key.encrypt(block)
            decrypted_blocks.append(decrypted_block)

        return b''.join(decrypted_blocks)

    def _send_content(
            self, request_type: Type[PushMessageRequest],
            receiver_client_id: int, content: Optional[bytes] = b'',
    ) -> str:
        from protocol.packets.request.messages import SendMessageRequest, \
            SendSymmetricKeyRequest, SendFileRequest, GetSymmetricKeyRequest
        request = request_type()
        request_fields = {
            'receiver_client_id': receiver_client_id,
            'sender_client_id': self.client_id,
        }

        if isinstance(request, (SendMessageRequest, SendFileRequest, )):
            assert content != b'', "Can't send an empty message."
            request_fields['content'] = \
                self._encrypt_with_symmetric_key(
                    content=content,  # noqa
                    requested_client_id=receiver_client_id,
                )
        elif isinstance(request, SendSymmetricKeyRequest):
            public_key = self._get_public_key_of_client(receiver_client_id)
            request_fields['content'] = \
                self._encrypt_symmetric_key_with_public_key(
                    symmetric_key=content,
                    public_key=public_key,
                )
        elif isinstance(request, GetSymmetricKeyRequest):
            request_fields['content'] = b''
        else:
            raise ClientAppException(f"Unexpected request {request}.")

        response_fields = self.handler.handle(request, request_fields)
        receiver_client_id = response_fields['receiver_client_id']
        message_id = response_fields['message_id']
        return f"Message {message_id} sent to client with ID " \
               f"{receiver_client_id}."

    def _pop_messages(self) -> str:
        from protocol.packets.request.requests import PopMessagesRequest
        from protocol.fields.message import Messages
        from protocol.packets.request.messages import GetSymmetricKeyRequest, \
            SendSymmetricKeyRequest

        request = PopMessagesRequest()
        fields_to_pack = {'sender_client_id': self.client_id}
        response_fields = self.handler.handle(request, fields_to_pack)

        messages = response_fields['messages']
        if len(messages) == 0:
            return "You don't have any unread messages."

        messages_strings = []
        assert len(messages) % len(Messages().fields) == 0
        fields_count = len(Messages().fields)
        for idx in range(len(messages) // fields_count):
            from_client_id = messages[idx * fields_count]
            message_type = messages[idx * fields_count + 2]
            content = messages[idx * fields_count + 4]

            # TODO: split to methods
            if message_type == GetSymmetricKeyRequest.MESSAGE_TYPE:
                content = "Request for symmetric key"
            elif message_type == SendSymmetricKeyRequest.MESSAGE_TYPE:
                logging.info(
                    f"Trying to get public key and decrypt symmetric key")
                public_key = \
                    str(self._get_public_key_of_client(self.client_id))
                self.client_ids_to_symmetric_keys[from_client_id] = \
                    self._decrypt_symmetric_key_with_private_key(
                        encrypted_symmetric_key=content,
                        public_key_pem=public_key,
                    )
                content = "Symmetric key received"
            else:  # message OR file
                content = self._decrypt_with_symmetric_key(
                    content, from_client_id)

            message_string = \
                f"From: {from_client_id}\n" \
                f"Content:\n" \
                f"{content!s}\n" \
                F"-----<EOM>-----"
            messages_strings.append(message_string)
        return '\n'.join(messages_strings)

    def _send_message(self):
        """Sends text message written by user."""
        from protocol.packets.request.messages import SendMessageRequest

        requested_client_id = self._get_client_id()
        message = input("Enter message: ")

        return self._send_content(
            request_type=SendMessageRequest,
            receiver_client_id=requested_client_id,
            content=message.encode(),
        )

    def _send_file(self) -> str:
        """Tries reading and sending file content as requested by user."""
        from protocol.packets.request.messages import SendFileRequest

        requested_client_id = self._get_client_id()
        pathname = input("Enter pathname: ")
        if not os.path.exists(pathname):
            raise ClientAppException(f"No file at: {pathname}.")
        with open(pathname, 'r') as file:
            file_content = file.read()

        return self._send_content(
            request_type=SendFileRequest,
            receiver_client_id=requested_client_id,
            content=file_content.encode(),
        )

    def _get_symmetric_key(self) -> str:
        """Sends a get symmetric key request."""
        from protocol.packets.request.messages import GetSymmetricKeyRequest
        receiver_client_id = self._get_client_id()
        return self._send_content(
            request_type=GetSymmetricKeyRequest,
            receiver_client_id=receiver_client_id,
        )

    def _send_symmetric_key(self):
        """Prompts user for client, gets requested client's public key,
          generates an AES-CBC key, saves it locally, encrypts the symmetric
          key with the public key, and sends to the requested client."""
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
        from protocol.packets.request.messages import SendSymmetricKeyRequest

        requested_client_id = self._get_client_id()
        aes_key = get_random_bytes(ClientApp.AES_256_KEY_BYTES)
        aes_cbc_key = AES.new(
            key=aes_key,
            iv=ClientApp.AES_IV,
            mode=AES.MODE_CBC,
        )
        self.client_ids_to_symmetric_keys[requested_client_id] = aes_cbc_key

        return self._send_content(
            request_type=SendSymmetricKeyRequest,
            receiver_client_id=requested_client_id,
            content=aes_key,
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

            # TODO:
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
                last_command_output = action(self)  # noqa


def run():
    client = ClientApp()
    client.run()
