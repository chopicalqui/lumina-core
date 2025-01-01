# This file is part of Lumina.
#
# Lumina is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lumina is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lumina. If not, see <https://www.gnu.org/licenses/>.

__author__ = "Lukas Reiter"
__copyright__ = "Copyright (C) 2024 Lukas Reiter"
__license__ = "GPLv3"

import hashlib
from uuid import UUID
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pydantic import BaseModel, Field as PydanticField, AliasChoices

from .status import StatusMessage
from ..models.account import Account


class LuminaError(Exception):
    """
    Base class for all exceptions in this application.
    """
    def __init__(
            self,
            message: str | None = None,
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message)
        self.account = account
        self.exc = exc


class NotFoundError(LuminaError):
    """
    Raised when an object is not found in the database.
    """
    def __init__(
            self,
            message: str = "Object not found.",
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message, account, exc)
        self.status_code = 404


class InvalidDataError(LuminaError):
    """
    Raised when data could not be updated.
    """
    def __init__(
            self,
            message: str | None = "Invalid data.",
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message, account, exc)
        self.status_code = 400


class IdpConnectionError(LuminaError):
    """
    Raised when connecting to IdP failed.
    """
    def __init__(
            self,
            message: str | None = "Connection to IdP failed.",
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message, account, exc)
        self.status_code = 500


class AuthorizationError(LuminaError):
    """
    Raised when account authorization failed.
    """
    def __init__(
            self,
            message: str | None = "Authorization failed.",
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message, account, exc)
        self.status_code = 403


class AuthenticationError(LuminaError):
    """
    Raised when account authentication/authorization failed.
    """
    def __init__(
            self,
            message: str | None = "Authentication failed.",
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message, account, exc)
        self.status_code = 401


class NotNullConstraintError(LuminaError):
    """
    Raised when database update violates a NOT NULL constraint.
    """
    def __init__(
            self, message: str | None = None,
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message, account, exc)
        self.status_code = 400


class UniqueConstraintError(LuminaError):
    """
    Raised when database update violates a unique constraint.
    """
    def __init__(
            self, message: str | None = None,
            account: Account | None = None,
            exc: Exception | None = None
    ):
        super().__init__(message, account, exc)
        self.status_code = 400


class AccountLookup(BaseModel):
    id: UUID
    full_name: str = PydanticField(
        serialization_alias="label",
        validation_alias=AliasChoices("label", "full_name")
    )


def enum_to_str(enum, default_value: str = None) -> str | None:
    """
    Converts an enum to a string.
    """
    result = default_value
    if enum is not None:
        result = " ".join([item.capitalize() for item in enum.name.split("_")])
    return result


def sha256(string: str) -> str:
    """
    Returns the SHA-256 hash of a string.
    """
    return hashlib.sha256(string.strip().encode("utf-8")).hexdigest()


def hmac_sha256(data: str, key: str) -> str:
    """
    Returns the HMAC-SHA256 hash of a string.
    """
    if not key:
        raise ValueError("HMAC key is empty.")
    h = hmac.HMAC(key.encode(), hashes.SHA256())
    h.update(data.encode())
    # Generate the HMAC (keyed hash)
    digest = h.finalize()
    return digest.hex()
