from datetime import timedelta, datetime, timezone
from typing import Optional

import jwt
from fastapi import HTTPException
from pydantic import SecretStr
from starlette import status

from src.security.interfaces import JWTAuthInterface


class JWTManager(JWTAuthInterface):
    def __init__(
        self,
        secret_key_access: SecretStr,
        secret_key_refresh: SecretStr,
        algorithm: str,
    ):
        self._secret_key_access = secret_key_access.get_secret_value()
        self._secret_key_refresh = secret_key_refresh.get_secret_value()
        self._algorithm = algorithm

    @property
    def access_token_expiry(self) -> timedelta:
        return timedelta(minutes=60)

    @property
    def refresh_token_expiry(self) -> timedelta:
        return timedelta(days=7)

    def __create_token(
        self, data: dict, secret_key: str, expires_delta: timedelta | None = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=self._algorithm)
        return encoded_jwt

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        return self.__create_token(
            data, self._secret_key_access, expires_delta or self.access_token_expiry
        )

    def create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        return self.__create_token(
            data, self._secret_key_refresh, expires_delta or self.refresh_token_expiry
        )

    def decode_token(self, token: str, is_refresh: bool = False) -> dict:
        secret = self._secret_key_refresh if is_refresh else self._secret_key_access
        try:
            payload = jwt.decode(token, secret, algorithms=[self._algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
