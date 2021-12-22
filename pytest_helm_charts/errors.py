class WaitTimeoutError(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class ObjectStatusError(Exception):
    def __init__(self, msg: str):
        self.msg = msg
