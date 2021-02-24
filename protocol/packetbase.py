import abc
from typing import Union, Tuple


class PacketBase(metaclass=abc.ABCMeta):
    """Abstract packet base class in MessageU protocol.

    Attributes:
      FIELDS_TO_TYPE_AND_LENGTH: Mapping from field name to it's corresponding
        Python type presentation, and the packet field length in bytes.
      VERSION: Unique version of server / client. Either 1 or 2.
      CODE: Unique packet code. Each full packet implementation has a
        different code.
    """

    PAYLOAD_SIZE_LENGTH = 4

    FIELDS_TO_TYPE_AND_LENGTH = {
        'client_id': (int, 16),
        'version': (int, 1),
        'payload_size': (int, PAYLOAD_SIZE_LENGTH),
        'name': (str, 255),
        'public_key': (bytes, 160),
        'message_type': (int, 1),
    }

    @property
    @abc.abstractmethod
    def VERSION(self) -> int: pass
    @property
    @abc.abstractmethod
    def CODE(self) -> int: pass
    @property
    @abc.abstractmethod
    def HEADER_FIELDS(self) -> Tuple[str]: pass

    HEADER_FIELDS_TO_TYPE_AND_LENGTH = {
        field for field in FIELDS_TO_TYPE_AND_LENGTH if field in HEADER_FIELDS
    }

    HEADER_LENGTH = sum(
        header_field[1]
        for header_field in HEADER_FIELDS_TO_TYPE_AND_LENGTH
    )

    @classmethod
    def _int_to_bytes(cls, name: str, value: int, length: int) -> bytes:
        max_value = 2 ** length - 1
        if value > max_value:
            raise ValueError(
                f"'{name}' value '{value}' exceeds the {length} "
                f"bytes length of field.")
        return value.to_bytes(
            length=length,
            byteorder="little",
            signed=False,
        )

    @classmethod
    def _str_to_bytes(cls, name: str, value: str, length: int) -> bytes:
        if len(value) > length:
            raise ValueError(
                f"'{name}' value '{value}' exceeds the {length} "
                f"bytes length of field.")
        return value.encode().zfill(length)

    @classmethod
    def _validate_bytes_length(
            cls, name: str, value: bytes, length: int,
    ) -> bytes:
        if len(value) != length:
            raise ValueError(
                f"'{name}' value '{value}' is not of {length} "
                f"bytes length of field.")
        return value

    @classmethod
    def field_to_bytes(cls, name: str, value: Union[int, str]) -> bytes:
        field_type, length = cls.FIELDS_TO_TYPE_AND_LENGTH[name]
        if field_type is int:
            return cls._int_to_bytes(name, value, length)
        elif field_type is str:
            return cls._str_to_bytes(name, value, length)
        elif field_type is bytes:
            return cls._validate_bytes_length(name, value, length)
        else:
            raise ValueError(f"Invalid type {field_type} for field {name}.")

    def __init__(self, payload: bytes = b''):
        """
        Initializes packet with base fields and payload.

        Args:
            payload: packet payload in bytes
        """
        self.version_bytes = PacketBase.field_to_bytes('version', self.VERSION)
        self.code_bytes = PacketBase.field_to_bytes('code', self.CODE)
        self.payload_size_bytes = PacketBase.field_to_bytes(
            'payload_size', len(payload))
        self.payload = payload

    def __str__(self):
        """Returns string with basic attributes. Used for debug logging."""
        return "{}(code={}, length={})".format(
            self.__class__.__name__,
            self.CODE,
            len(self.payload),
        )

    def create(self) -> bytes:
        """Returns the entire encoded message in bytes."""
        return self.version_bytes + self.code_bytes + \
            self.payload_size_bytes + self.payload
