class SeedessError(Exception):
    """A non-2xx Seedess response."""

    def __init__(self, status: int, code: str, message: str, body=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.body = body
