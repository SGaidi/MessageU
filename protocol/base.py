from abc import ABC
from typing import Union


class Base(ABC):

    @property
    def VERSION(self) -> Union[1, 2]:
        raise NotImplementedError(
            f"VERSION must be defined in child classes.")

    VERSION_LENGTH = 1

    @property
    def CODE(self) -> int:
        raise NotImplementedError(f"Should be defined in child classes.")

    @property
    def CODE_LENGTH(self) -> int:
        raise NotImplementedError(f"Should be defined in child classes.")

    PAYLOAD_SIZE_LENGTH = 4

    CLIENT_ID_LENGTH = 16
    NAME_LENGTH = 255
    MESSAGE_TYPE_LENGTH = 1

    @classmethod
    def int_to_bytes(cls, param: int, length: int) -> bytes:
        return param.to_bytes(
            length=length,
            byteorder="little",
            signed=False,
        )

    def __init__(self, payload: bytes = b''):
        """
        Args:
            payload: message content in bytes
        """
        self.version = Base.int_to_bytes(
            param=self.VERSION, length=self.VERSION_LENGTH)
        self.code = Base.int_to_bytes(
            param=self.CODE, length=self.CODE_LENGTH)
        self.payload = payload
        self.payload_size = Base.int_to_bytes(
            param=len(self.payload), length=Base.PAYLOAD_SIZE_LENGTH)
