class Client:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
    def login(self) -> None:
        ... # TODO client.api.login