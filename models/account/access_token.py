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

import sqlalchemy as sa
from enum import Enum
from uuid import UUID
from typing import List, Set, Dict
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field as PydanticField, computed_field
from sqlmodel import SQLModel, Field, Column, ForeignKey, Relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects import postgresql

from core.models.account import ApiPermissionEnum


class AccessTokenType(Enum):
    user = 10
    api = 20


class AccessToken(SQLModel, table=True):
    """
    Store information about an account tokens in the database.
    """
    id: UUID = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs=dict(server_default=func.gen_random_uuid()),
        description="The unique identifier of the token."
    )
    name: str | None = Field(description="The name of the token. Only used for API access tokens.")
    type: AccessTokenType = Field(description="The type of the token.")
    scopes: Set[ApiPermissionEnum] | None = Field(
        default={},
        sa_column=Column(postgresql.ARRAY(sa.Enum(ApiPermissionEnum))),
        description="The scopes of the token."
    )
    revoked: bool = Field(
        sa_column_kwargs=dict(server_default='false'),
        description="Indicates if the token has been revoked."
    )
    expiration: datetime | None = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
        description="The expiration date of the token."
    )
    checksum: str = Field(
        index=True,
        unique=True,
        description="The SHA256 value of the JWT. Used for token validation and revocation."
    )
    # Internal information only
    created_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        description="The date and time when the token was created."
    )
    last_modified_at: datetime | None = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        description="The date and time when the token was last modified."
    )
    # Foreign keys
    account_id: UUID = Field(
        default=None,
        sa_column=Column(
            postgresql.UUID(as_uuid=True),
            ForeignKey("account.id", ondelete="CASCADE"),
            nullable=False
        ),
        description="Foreign key to the account that owns the token."
    )
    # Relationship definitions
    account: "Account" = Relationship(
        back_populates="tokens"
    )


class AccessTokenCreateUpdateBase(BaseModel):
    """
    Represents the base schema for updating or creating a JWT.
    """
    model_config = ConfigDict(from_attributes=True)


class AccessTokenCreate(AccessTokenCreateUpdateBase):
    """
    Schema for creating a JWT. It is used by the FastAPI to create a new JWT.
    """
    name: str = PydanticField(description="The name of the token.")
    scopes: List[str] = PydanticField(description="The scopes of the token.")
    expiration: datetime = PydanticField(description="The expiration date and time of the token.")


class AccessTokenRead(AccessTokenCreateUpdateBase):
    """
    Schema for reading a JWT (without token value). It is used by the FastAPI to read a JWT.
    """
    id: UUID
    name: str | None = PydanticField(default=None)
    scope_: List[ApiPermissionEnum] = PydanticField(
        exclude=True,
        validation_alias="scopes",
        description="The scopes of the token."
    )
    expiration_: datetime  | None= PydanticField(
        default=None,
        exclude=True,
        validation_alias="expiration",
        description="The expiration date and time of the token."
    )
    revoked: bool
    created_at: datetime

    @computed_field
    def scopes(self) -> List[Dict[str, str]]:
        """
        Converts the scopes to a set of enums.
        """
        return [{"id": item.name, "label": item.value.description} for item in self.scope_]

    @computed_field
    def expiration(self) -> date | None:
        """
        Converts the scopes to a set of enums.
        """
        return self.expiration_.date() if self.expiration_ else None


class AccessTokenReadTokenValue(AccessTokenRead):
    """
    Schema for reading a JWT including token value. It is used by the FastAPI to read a JWT.
    """
    value: str


class AccessTokenUpdate(BaseModel):
    """
    Schema for updating a JWT. It is used by the FastAPI to update a JWT.
    """
    id: UUID
    revoked: bool
