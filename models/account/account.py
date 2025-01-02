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
from enum import IntEnum
from uuid import UUID
from datetime import date, datetime
from typing import List, Set, Dict
from pydantic import BaseModel, Field as PydanticField, ConfigDict, AliasChoices
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects import postgresql
from .access_token import AccessTokenType, AccessToken
from .notification import Notification, Notify
from .role import RoleEnum, ROLE_PERMISSION_MAPPING
from .mui_data_grid import MuiDataGrid
from ...utils.status import StatusMessage


class AccountType(IntEnum):
    """
    Category of account types.
    """
    personal = 10
    technical = 20
    obsolete = 30


class TableDensityType(IntEnum):
    """
    Material UI DataGrid table density types.
    """
    comfortable = 0
    standard = 10
    compact = 20


class Account(SQLModel, table=True):
    """
    Store information about an account in the database.
    """
    id: UUID = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs=dict(server_default=func.gen_random_uuid()),
        description="The unique identifier of the account."
    )
    email: str = Field(
        index=True,
        unique=True,
        description="The email address of the account."
    )
    locked: bool = Field(
        sa_column_kwargs=dict(server_default='false'),
        description="Indicates if the account has been locked."
    )
    type: AccountType = Field(
        sa_column_kwargs=dict(server_default=AccountType.personal.name),
        description="The type of account."
    )
    full_name: str = Field(description="The full name of the account.")
    active_from: date = Field(
        sa_column_kwargs=dict(server_default=func.now()),
        description="The date when the account becomes active. Before this date, the account cannot log in."
    )
    active_until: date | None = Field(
        description="The date when the account becomes inactive. After this date, the account cannot log in."
    )
    # Account settings
    light_mode: bool = Field(
        sa_column_kwargs=dict(server_default='true'),
        description="Indicates if the account prefers the light mode."
    )
    sidebar_collapsed: bool = Field(
        sa_column_kwargs=dict(server_default='false'),
        description="Indicates if the account prefers the detailed UI menu."
    )
    table_density: TableDensityType = Field(
        sa_column_kwargs=dict(server_default=TableDensityType.compact.name),
        description="The preferred table density of the MUI DataGrids."
    )
    avatar: bytes | None = Field(description="The account's avatar image.")
    roles: Set[RoleEnum] = Field(
        default={},
        sa_column=Column(postgresql.ARRAY(sa.Enum(RoleEnum))),
        description="The roles of the account."
    )
    # Internal information only
    last_login: datetime | None = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
        description="The date and time when the account last logged in."
    )
    created_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        description="The date and time when the account was created."
    )
    last_modified_at: datetime | None = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        description="The date and time when the account was last modified."
    )
    # Relationship definitions
    tokens: List[AccessToken] = Relationship(
        back_populates="account", cascade_delete=True
    )
    notifications: List[Notification] = Relationship(
        sa_relationship_kwargs=dict(
            back_populates="account",
            order_by="desc(Notification.created_at)",
            lazy='selectin'
        ),
        cascade_delete=True
    )
    data_grids: List[MuiDataGrid] = Relationship(
        sa_relationship_kwargs=dict(
            back_populates="account",
            lazy='selectin'
        ),
        cascade_delete=True
    )

    @property
    def roles_str(self) -> List[str]:
        """
        Returns all account roles as a list of strings.
        """
        return [item.name for item in self.roles]

    @property
    def scopes_str(self) -> List[str]:
        """
        Returns all REST API permissions/scopes.
        """
        result = []
        for role in self.roles:
            result.extend([item for item in ROLE_PERMISSION_MAPPING[role.name]])
        return list(set(sorted(result)))

    def is_active(self) -> bool:
        """
        Returns True if the account is active.
        """
        return not self.locked and \
               self.active_from <= date.today() and \
               (not self.active_until or self.active_until > date.today())

    def get_access_token(self, name: str) -> str | None:
        """
        Returns the account's access token by name.
        """
        result = [item for item in self.tokens if item.name == name and item.type == AccessTokenType.api]
        if not result:
            return None
        return result[0].value

    def get_data_grid(self, settings_id: UUID) -> Dict:
        """
        Returns the account's Material UI DataGrid configuration by settings_id.
        """
        result = [item for item in self.data_grids if item.settings_id == settings_id]
        if not result:
            return {}
        return result[0].settings

    def get_data_grid_filters(self, settings_id: UUID) -> List[Dict]:
        """
        Returns the account's Material UI DataGrid filter configurations by settings_id.
        """
        result = [item for item in self.data_grids if item.settings_id == settings_id]
        if not result:
            return []
        return [item.filter for item in result[0].filters]

    async def notify(self, session: AsyncSession, message: Notify, dedup: bool = True):
        """
        Send the account a notification.
        """
        unread_duplicates = [item for item in self.notifications if item.message == message and not item.read]
        if not dedup or len(unread_duplicates) == 0:
            session.add(Notification(**message.dict(), account_id=self.id))
        else:
            for item in unread_duplicates:
                item.created_at = func.now()


class AccountTest(BaseModel):
    """
    This is the account schema. It is used by pytest to create and manage test accounts during unittests.
    """
    id: UUID | None = PydanticField(None)
    email: str
    full_name: str
    bearer: str | None = PydanticField(None)
    roles: Set[RoleEnum]
    locked: bool | None | None = PydanticField(None)
    avatar: bytes | None = PydanticField(None)
    active_from: date | None = PydanticField(None)
    active_until: date | None | None = PydanticField(None)
    created_at: datetime | None = PydanticField(None)
    last_modified_at: datetime | None = PydanticField(None)
    last_login: datetime | None = PydanticField(None)

    @staticmethod
    def get_auth_header(bearer: str) -> Dict[str, str]:
        """
        Returns a cookie header with the bearer token.
        """
        return {'Cookie': f'access_token={bearer}'}

    @staticmethod
    def get_empty_auth_header() -> Dict[str, str]:
        return {'Cookie': f'access_token='}

    def get_authentication_header(self) -> Dict[str, str]:
        """
        Returns a cookie header with the bearer token.
        """
        return AccountTest.get_auth_header(self.bearer)


class AccountRead(BaseModel):
    """
    This is the account schema. It is used by the FastAPI to read an account.
    """
    model_config = ConfigDict(
        use_enum_values=False,
        extra="ignore",
        json_encoders={
            TableDensityType: lambda x: x.name
        }
    )

    id: UUID
    email: str
    full_name: str
    roles: Set[RoleEnum]
    locked: bool | None = PydanticField(default=None)
    active_from: date | None = PydanticField(default=None)
    active_until: date | None = PydanticField(default=None)
    last_login: datetime | None = PydanticField(default=None)


class WebSocketNotifyAccount(BaseModel):
    """
    Schema for notifying accounts via the message queue and WebSockets.
    """
    account: Account
    status: StatusMessage


class AccountReadMe(AccountRead):
    """
    This is the account schema. It is used by the FastAPI to read an account.
    """
    light_mode: bool
    sidebar_collapsed: bool
    table_density: TableDensityType
    avatar: str | None = PydanticField(default=None)


class AccountUpdateAdmin(SQLModel):
    """
    This is the account schema. It is used by the FastAPI to update an account.
    """
    model_config = ConfigDict(extra="ignore")

    id: UUID
    locked: bool | None = PydanticField(default=None)
    active_from: date = PydanticField(
        default=None,
        validation_alias=AliasChoices("active_from", "activeFrom")
    )
    active_until: date | None = PydanticField(
        default=None,
        validation_alias=AliasChoices("active_until", "activeUntil")
    )
