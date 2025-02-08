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
from uuid import UUID
from datetime import datetime
from typing import Dict, List, Any
from pydantic import Field as PydanticField, BaseModel
from sqlmodel import SQLModel, Field, Column, ForeignKey, Relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects import postgresql


class MuiDataGridFilter(SQLModel, table=True):
    """
    Store information about an account's Material UI DataGrid filter configuration.
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
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        description="The date and time when the filter was created."
    )
    last_modified_at: datetime | None = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        description="The date and time when the filter was last modified."
    )
    # Foreign keys
    data_grid_id: UUID = Field(
        sa_column=Column(
            postgresql.UUID(as_uuid=True),
            ForeignKey("muidatagrid.id", ondelete="CASCADE", name="fk_filter_data_grid_id")
        ),
        description="Foreign key to the data grid that the filter belongs to."
    )
    # Relationship definitions
    data_grid: "MuiDataGrid" = Relationship(
        back_populates="filters",
        sa_relationship_kwargs=dict(
            foreign_keys="[MuiDataGridFilter.data_grid_id]"
        )
    )


class FilterModel(BaseModel):
    """
    Handles filtering logic and options for the MUI DataGrid, including quick filters and logic operators
    """
    items: List[Any] = Field(default=[])
    logicOperator: str = Field(default="and")
    quickFilterValues: List[Any] = Field(default=[])
    quickFilterLogicOperator: str = Field(default="and")


class Filter(BaseModel):
    """
    Wraps the filter model configuration for easier integration in the MUI DataGrid
    """
    filterModel: FilterModel


class MuiDataGridFilterLookup(BaseModel):
    """
    This is the Material UI DataGrid filter lookup schema. It is used by the FastAPI to read a filter.
    """
    id: UUID
    name: str = PydanticField(description="The name of the filter.", serialization_alias="label")
    filter: FilterModel


class MuiDataGridFilterCreate(BaseModel):
    """
    This is the Material UI DataGrid filter creation schema. It is used by the FastAPI to create a filter.
    """
    name: str = PydanticField(description="The name of the filter.", serialization_alias="label")
    data_grid_id: UUID
    filter: FilterModel


class MuiDataGridFilterUpdate(BaseModel):
    """
    Schema for updating a DataGrid's selected filter .
    """
    selected_filter_id: UUID | None = PydanticField(default=None, description="The ID of the selected filter.")
