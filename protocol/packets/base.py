import abc
import logging
from copy import deepcopy
from typing import Tuple, Any, NewType, Optional

from common.utils import abstractproperty, classproperty
from common.exceptions import PacketBaseValueError
from protocol.fields.base import FieldBase


class PacketBase(metaclass=abc.ABCMeta):
    """Abstract packet base class in MessageU protocol.

    Class Attributes:
      PacketBase: class typing hack.
      CODE: Unique packet code. Each concrete packet implementation has a
        different code.
      X_FIELD: Shortcut for creating specific fields.
    Attributes:
      header_fields: TODO:
      payload_fields: TODO:
    """

    PacketBase = NewType('PacketBase', type)  # only for type notations

    CODE = None

    payload_fields: Tuple[FieldBase, ...] = ()
    payload_size: int
    header_fields: Tuple[FieldBase, ...]

    @classmethod
    def _length_of_fields(cls, fields: Tuple[FieldBase, ...]) -> int:
        return sum(field.length for field in fields)

    @abstractproperty
    def HEADER_FIELDS_TEMPLATE(self) -> Tuple[FieldBase]: pass

    @classproperty
    def HEADER_LENGTH(self) -> int:
        return self._length_of_fields(self.HEADER_FIELDS_TEMPLATE)

    def _update_header_value(self, field_name: str, field_value: Any) -> None:
        for header in self.header_fields:
            if header.name == field_name:
                header.value = field_value
                return
        raise PacketBaseValueError(self, f"Invalid field name {field_name!s}!")

    CALCULATE_PAYLOAD_SIZE = -1

    def __init__(self, payload_size: Optional[int] = CALCULATE_PAYLOAD_SIZE):
        self.header_fields = deepcopy(self.HEADER_FIELDS_TEMPLATE)
        if payload_size == self.CALCULATE_PAYLOAD_SIZE:
            payload_str = ', '.join(str(f) for f in self.payload_fields)
            print({payload_str})
            payload_size = self._length_of_fields(self.payload_fields)
        self._update_header_value('payload_size', payload_size)
        self._update_header_value('code', self.CODE)

    def __str__(self):
        """Returns string with basic attributes."""
        headers_str = ', '.join(str(f) for f in self.header_fields)
        payload_str = ', '.join(str(f) for f in self.payload_fields)
        return f"{self.__class__.__name__}" \
               f"(code={self.CODE}, " \
               f"header=({headers_str}), " \
               f"payload=({payload_str}))"
