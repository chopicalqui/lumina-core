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


from uuid import UUID
from datetime import datetime
from typing import Dict, List
from pydantic import Field as PydanticField
from sqlmodel import SQLModel, Field, Column, ForeignKey, Relationship
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects import postgresql


class MuiDataGrid(SQLModel, table=True):
    """
    Store information about an account's Material UI DataGrid configuration.
    """

    id: UUID = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs=dict(server_default=func.gen_random_uuid()),
        description="The unique identifier of the data grid configuration."
    )
    settings_id: UUID = Field(
        index=True,
        description="The unique identifier of the data grid settings."
    )
    settings: Dict | None = Field(
        sa_column=Column(postgresql.JSON()),
        description="The data grid settings."
    )
    # Internal information only
    created_at: datetime = Field(
        sa_column_kwargs=dict(server_default=func.now()),
        description="The date and time when the configuration was created."
    )
    last_modified_at: datetime | None = Field(
        default=None,
        sa_column_kwargs=dict(onupdate=func.now()),
        description="The date and time when the configuration was last modified."
    )
    # Foreign keys
    account_id: UUID = Field(
        default=None,
        sa_column=Column(postgresql.UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE")),
        description="Foreign key to the account that the configuration belongs to."
    )
    # Relationship definitions
    account: "Account" = Relationship(back_populates="data_grids")
    filters: List["MuiDataGridFilter"] = Relationship(back_populates="data_grid")

    __table_args__ = (
        # TODO: Write unittest for postgresql_nulls_not_distinct
        UniqueConstraint('settings_id', 'account_id', postgresql_nulls_not_distinct=True),
    )


class MuiDataGridFilter(SQLModel, table=True):
    """
    Store information about a account's Material UI DataGrid filter configuration.
    """
    id: UUID = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs=dict(server_default=func.gen_random_uuid()),
        description="The unique identifier of the data grid filter configuration."
    )
    name: str = Field(description="The name of the filter.")
    filter: Dict | None = Field(
        default={},
        sa_column=Column(postgresql.JSON()),
        description="The data grid filter."
    )
    # Internal information only
    created_at: datetime = Field(
        sa_column_kwargs=dict(server_default=func.now()),
        description="The date and time when the filter was created."
    )
    last_modified_at: datetime | None = Field(
        default=None,
        sa_column_kwargs=dict(onupdate=func.now()),
        description="The date and time when the filter was last modified."
    )
    # Foreign keys
    data_grid_id: UUID = Field(
        default=None,
        sa_column=Column(postgresql.UUID(as_uuid=True), ForeignKey("muidatagrid.id", ondelete="CASCADE")),
        description="Foreign key to the data grid that the filter belongs to."
    )
    # Relationship definitions
    data_grid: List["MuiDataGrid"] = Relationship(back_populates="filters")


class MuiDataGridFilterRead(SQLModel):
    """
    This is the Material UI DataGrid filter schema. It is used by the FastAPI to read a filter.
    """
    id: UUID
    name: str
    filter: Dict | None = PydanticField(default=None)


class MuiDataGridFilterLookup(SQLModel):
    """
    This is the Material UI DataGrid filter lookup schema. It is used by the FastAPI to read a filter.
    """
    id: UUID
    name: str
