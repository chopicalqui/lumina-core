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
from pydantic import BaseModel, Field as PydanticField, AliasChoices


class LuminaException(Exception):
    """
    Base class for all exceptions in this application.
    """
    def __init__(self, message: str | None = None):
        super().__init__(message)


class NotFoundException(LuminaException):
    """
    Raised when an object is not found in the database.
    """

    def __init__(self, message: str | None = None):
        super().__init__(message)


class UserLookup(BaseModel):
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
