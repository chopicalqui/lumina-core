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

from enum import IntEnum
from uuid import UUID
from datetime import date, datetime
from typing import List, Set, Dict
from pydantic import BaseModel, Field as PydanticField, ConfigDict, computed_field
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import backref
from sqlalchemy.dialects import postgresql
from .token import TokenType, JsonWebToken
from .notification import Notification
from .role import RoleEnum, ROLE_PERMISSION_MAPPING
from .mui_data_grid import MuiDataGrid
from ...status import StatusMessage


class TableDensityType(IntEnum):
    """
    Material UI DataGrid table density types.
    """
    comfortable = 0
    standard = 10
    compact = 20


class User(SQLModel, table=True):
    """
    Store information about a user in the database.
    """
    __tablename__ = "user_data"
    id: UUID = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs=dict(server_default=func.gen_random_uuid()),
        description="The unique identifier of the user."
    )
    email: str = Field(
        index=True,
        unique=True,
        description="The email address of the user."
    )
    locked: bool = Field(
        sa_column_kwargs=dict(server_default='false'),
        description="Indicates if the user account has been locked."
    )
    full_name: str = Field(description="The full name of the user.")
    active_from: date = Field(
        sa_column_kwargs=dict(server_default=func.now()),
        description="The date when the user account becomes active. Before this date, the user cannot log in."
    )
    active_until: date | None = Field(
        description="The date when the user account becomes inactive. After this date, the user cannot log in."
    )
    # User settings
    light_mode: bool = Field(
        sa_column_kwargs=dict(server_default='true'),
        description="Indicates if the user prefers the light mode."
    )
    toggle_menu: bool = Field(
        sa_column_kwargs=dict(server_default='false'),
        description="Indicates if the user prefers the detailed UI menu."
    )
    table_density: TableDensityType = Field(
        sa_column_kwargs=dict(server_default=TableDensityType.compact.name),
        description="The preferred table density of the MUI DataGrids."
    )
    avatar: bytes | None = Field(description="The user's avatar image.")
    roles: Set[RoleEnum] = Field(
        default={},
        sa_column=Column(postgresql.ARRAY(Enum(RoleEnum))),
        description="The roles of the user."
    )
    # Internal information only
    last_login: datetime | None = Field(description="The date and time when the user last logged in.")
    created_at: datetime = Field(
        sa_column_kwargs=dict(server_default=func.now()),
        description="The date and time when the user was created."
    )
    last_modified_at: datetime | None = Field(
        sa_column_kwargs=dict(onupdate=func.now()),
        description="The date and time when the user was last modified."
    )
    # Relationship definitions
    tokens: List[JsonWebToken] = Relationship(
        sa_relationship_kwargs=dict(
            backref=backref("user", cascade="delete"),
        ),
        cascade_delete=True
    )
    notifications: List[Notification] = Relationship(
        sa_relationship_kwargs=dict(
            backref=backref("user", cascade="delete"),
            order_by="desc(Notification.created_at)"
        ),
        cascade_delete=True
    )
    data_grids: List[MuiDataGrid] = Relationship(
        sa_relationship_kwargs=dict(
            backref=backref("user", cascade="delete"),
        ),
        cascade_delete=True
    )

    @property
    def roles_str(self) -> List[str]:
        """
        Returns all user roles as a list of strings.
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

    @property
    def is_active(self) -> bool:
        """
        Returns True if the user is active.
        """
        return not self.locked and \
               self.active_from <= date.today() and \
               (not self.active_until or self.active_until > date.today())

    def get_access_token(self, name: str) -> str | None:
        """
        Returns the user's access token by name.
        """
        result = [item for item in self.tokens if item.name == name and item.type == TokenType.api]
        if not result:
            return None
        return result[0].value

    def get_data_grid(self, settings_id: UUID) -> Dict:
        """
        Returns the user's Material UI DataGrid configuration by settings_id.
        """
        result = [item for item in self.data_grids if item.settings_id == settings_id]
        if not result:
            return {}
        return result[0].settings

    def get_data_grid_filters(self, settings_id: UUID) -> List[Dict]:
        """
        Returns the user's Material UI DataGrid filter configurations by settings_id.
        """
        result = [item for item in self.data_grids if item.settings_id == settings_id]
        if not result:
            return []
        return [item.filter for item in result[0].filters]


class UserTest(BaseModel):
    """
    This is the user schema. It is used by pytest to create and manage test users during unittests.
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
        return UserTest.get_auth_header(self.bearer)


class UserRead(BaseModel):
    """
    This is the user schema. It is used by the FastAPI to read a user.
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


class NotifyUser(BaseModel):
    """
    Schema for notifying users via the message queue and WebSockets.
    """
    user: User
    status: StatusMessage


class UserReadMe(UserRead):
    """
    This is the user schema. It is used by the FastAPI to read a user.
    """
    light_mode: bool
    toggle_menu: bool
    avatar: bytes | None = PydanticField(None, exclude=True)
    table_density: TableDensityType

    @computed_field
    def has_avatar(self) -> bool:
        return self.avatar is not None


class UserUpdateAdmin(SQLModel):
    """
    This is the user schema. It is used by the FastAPI to update a user.
    """
    model_config = ConfigDict(extra="ignore")

    id: UUID
    locked: bool | None = PydanticField(default=None)
    show_in_dropdowns: bool | None = PydanticField(default=None)
    active_from: date | None = PydanticField(default=None)
    active_until: date | None = PydanticField(default=None)
