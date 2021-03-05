import abc

from protocol.fields.header import Version, ResponseCode, PayloadSize
from protocol.packets.base import PacketBase


class Response(PacketBase, metaclass=abc.ABCMeta):

    VERSION = 2

    HEADER_FIELDS_TEMPLATE = (
        Version(VERSION),
        ResponseCode(),
        PayloadSize(),
    )
