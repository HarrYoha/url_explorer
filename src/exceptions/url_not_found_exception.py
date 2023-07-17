class UrlNotFoundException(Exception):
    def __init__(self, message="Url not found or not parsed"):
        self.message = message
        super().__init__(self.message)
