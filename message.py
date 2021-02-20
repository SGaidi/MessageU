import client


class Message:

    id: int  # 4 bytes
    from_client: client.Client
    to_client: client.Client

