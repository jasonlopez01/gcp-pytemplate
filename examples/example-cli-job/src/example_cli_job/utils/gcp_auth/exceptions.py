class InvalidCredentialsOAuth2(Exception):
    """Exception raised for Invalid OAuth2 Credentials
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message