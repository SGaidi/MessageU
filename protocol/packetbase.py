import abc
from itertools import islice
from typing import Union, Tuple, Dict, Any, Iterator, Type, NewType, List

from protocol.utils import classproperty


class PacketBase(metaclass=abc.ABCMeta):
    """Abstract packet base class in MessageU protocol.

    Attributes:
      FIELDS_TO_TYPE_AND_LENGTH: Mapping from field name to it's corresponding
        Python type presentation, and the packet field length in bytes.
      VERSION: Unique version of server / client. Either 1 or 2.
      CODE: Unique packet code. Each full packet implementation has a
        different code.
    """

    PacketBase = NewType('PacketBase', type)  # only for type notations

    PAYLOAD_SIZE_LENGTH = 4

    FIELDS_TO_TYPE_AND_LENGTH = {
        'client_id': (int, 16),
        'version': (int, 1),
        'payload_size': (int, PAYLOAD_SIZE_LENGTH),
        'name': (str, 255),
        'public_key': (bytes, 160),  # TODO: add encoding validator
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

    @classproperty
    def HEADER_FIELDS_TO_TYPE_AND_LENGTH(self) -> Dict[str, Tuple[type, int]]:
        return {
            field: value for field, value in
            self.FIELDS_TO_TYPE_AND_LENGTH.items()
            if field in self.HEADER_FIELDS
        }

    @classproperty
    def HEADER_LENGTH(self) -> int:
        return sum(
            header_field[1]
            for header_field in self.HEADER_FIELDS_TO_TYPE_AND_LENGTH.values()
        )

    @property
    @abc.abstractmethod
    def PAYLOAD_FIELDS(self) -> Tuple[str]: pass

    PAYLOAD_FIELDS_REPEAT = False

    def _int_to_bytes(self, name: str, value: int, length: int) -> bytes:
        bits_count = length * 8
        max_value = 2 ** bits_count - 1
        if value > max_value:
            raise ValueError(
                f"{name!r} value {value!r} exceeds the {length!r} "
                f"bytes length of field.")
        return value.to_bytes(
            length=length,
            byteorder="little",
            signed=False,
        )

    def _str_to_bytes(self, name: str, value: str, length: int) -> bytes:
        if len(value) > length:
            raise ValueError(
                f"'{name}' value '{value}' exceeds the {length} "
                f"bytes length of field.")
        return value.encode().zfill(length)

    def _validate_bytes_length(
            self, name: str, value: bytes, length: int,
    ) -> bytes:
        if len(value) != length:
            raise ValueError(
                f"'{name}' value '{value}' is not of {length} "
                f"bytes length of field. It is of length {len(value)}.")
        return value

    def field_to_bytes(self, name: str, value: Union[int, str]) -> bytes:
        try:
            field_type, length = self.FIELDS_TO_TYPE_AND_LENGTH[name]
        except Exception as e:
            raise Exception(f"Look!!! {e}")
        if field_type is int:
            return self._int_to_bytes(name, value, length)
        elif field_type is str:
            return self._str_to_bytes(name, value, length)
        elif field_type is bytes:
            return self._validate_bytes_length(name, value, length)
        else:
            raise ValueError(f"Invalid type {field_type} for field {name}.")

    def __init__(self, payload: bytes = b''):
        """
        Initializes packet with base fields and payload.

        Args:
            payload: packet payload in bytes
        """
        self.version_bytes = self.field_to_bytes('version', self.VERSION)
        self.code_bytes = self.field_to_bytes('code', self.CODE)
        self.payload_size_bytes = self.field_to_bytes(
            'payload_size', len(payload))
        self.payload = payload

    def __str__(self):
        """Returns string with basic attributes. Used for debug logging."""
        return "{}(code={}, length={})".format(
            self.__class__.__name__,
            self.CODE,
            len(self.payload),
        )

    def pack(self) -> bytes:
        """Returns the encoded message in bytes."""
        return self.version_bytes + self.code_bytes + \
            self.payload_size_bytes + self.payload

    @classmethod
    def _unpack_field(
            cls, field_name: str, content_iter: Iterator[bytes],
    ) -> Any:
        python_type, field_length = \
            cls.FIELDS_TO_TYPE_AND_LENGTH[field_name]

        field_bytes = bytes(islice(content_iter, field_length))

        if python_type is int:
            converted_field = int.from_bytes(
                bytes=field_bytes,
                byteorder="little",
                signed=False,
            )
        elif python_type is str:
            converted_field = bytes(field_bytes).decode().lstrip('0')
        else:
            converted_field = field_bytes

        return converted_field

    @classmethod
    def _unpack_bytes(
            cls, content: bytes, expected_field_names: Tuple[str],
    ) -> Dict[str, Any]:
        fields = {}
        content_iter = iter(content)
        import logging

        for field_name in expected_field_names:
            logging.debug(f'{field_name}')
            field_value = cls._unpack_field(
                field_name=field_name,
                content_iter=content_iter,
            )
            fields[field_name] = field_value

        return fields

    @classmethod
    def _validate_version(cls, version: int) -> None:
        if version != cls.VERSION:
            raise ValueError

    @classmethod
    def _validate_payload_size(cls, payload_size: int) -> None:
        if not payload_size >= 0:
            raise ValueError

    @classmethod
    def _validate_header_fields(
            cls, header_fields: Dict[str, Any],
    ) -> None:
        cls._validate_version(header_fields['version'])
        cls._validate_payload_size(header_fields['payload_size'])

    @classmethod
    def unpack_packet_base(cls, packet_header: bytes) -> Dict[str, Any]:
        header_fields = cls._unpack_bytes(
            content=packet_header, expected_field_names=cls.HEADER_FIELDS)
        cls._validate_header_fields(header_fields)
        return header_fields

    @classmethod
    def get_concrete_packet_type(cls, code: int) -> Type[PacketBase]:
        for packet in cls.ALL:
            if code == packet.CODE:
                return packet
        raise ValueError

    @classmethod
    def unpack_packet_payload(cls, payload: bytes) -> Union[Dict[str, Any], List]:
        if not cls.PAYLOAD_FIELDS_REPEAT:
            return cls._unpack_bytes(
                content=payload, expected_field_names=cls.PAYLOAD_FIELDS)

        repeat_count = payload / cls.PAYLOAD_SIZE_LENGTH
        if payload % cls.PAYLOAD_SIZE_LENGTH != 0:
            raise ValueError()
        dataset = []
        for _ in range(repeat_count):
            dataset.append(cls._unpack_bytes(
                content=payload, expected_field_names=cls.PAYLOAD_FIELDS
            ))
        return dataset
