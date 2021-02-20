

class Client:

    id: int  # 16 bytes
    name: str  # 255 bytes
    public_key: bytes  # 160 bytes

    def request(self):
        pass
