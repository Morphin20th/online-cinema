from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional


class JWTAuthInterface(ABC):
    @abstractmethod
    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        An abstract method for creating an access token.

        Parameters:
            data (dict): The payload data to encode within the token.
            expires_delta (Optional[timedelta]): The duration until the token expires. If not
                provided, a default expiration time should be used.

        Returns:
            str: The generated access token as a string.
        """
        pass

    @abstractmethod
    def create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        An abstract method for creating a refresh token.

        Parameters:
        data (dict): The payload of the token to be encoded.
        expires_delta (Optional[timedelta]): An optional parameter specifying the
            expiration duration for the token. If not provided, a default expiration
            may be applied by the implementation.

        Returns:
        str: The generated refresh token.
        """
        pass

    @abstractmethod
    def decode_token(self, token: str, is_refresh: bool = False) -> dict:
        """Decodes a JWT token and returns the payload as a dictionary.

        Parameters:
            token (str): The JWT token to decode.
            is_refresh (bool): Whether the token is a refresh token. Defaults to False.

        Returns:
            dict: The decoded token payload.
        """
        pass
