import abc

from protocol.fields.header import Version, RequestCode, PayloadSize, \
    SenderClientID
from protocol.packets.base import PacketBase


class Request(PacketBase, metaclass=abc.ABCMeta):
    """Abstract class of a request in MessageU protocol."""

    VERSION = 2

    HEADER_FIELDS_TEMPLATE = (
        Version(VERSION),
        RequestCode(),
        PayloadSize(),
        SenderClientID(),
    )

    def __init__(self):
        if self.__class__.__name__ == 'Request':
            # if it's not a concrete request - we don't know the payload
            super(Request, self).__init__(payload_size=None)
        else:
            super(Request, self).__init__()
