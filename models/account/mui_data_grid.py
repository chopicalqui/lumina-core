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
from pydantic import Field as PydanticField, BaseModel, field_validator
from sqlmodel import SQLModel, Field, Column, ForeignKey, Relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects import postgresql

from .mui_data_grid_filter import MuiDataGridFilter, Filter


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
    selected_filter_id: UUID | None = Field(
        sa_column=Column(
            postgresql.UUID(as_uuid=True),
            ForeignKey("muidatagridfilter.id", ondelete="SET NULL")
        ),
        description="The currently selected filter."
    )
    # Internal information only
    created_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        description="The date and time when the configuration was created."
    )
    last_modified_at: datetime | None = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        description="The date and time when the configuration was last modified."
    )
    # Foreign keys
    account_id: UUID = Field(
        sa_column=Column(postgresql.UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE")),
        description="Foreign key to the account that the configuration belongs to."
    )
    # Relationship definitions
    account: "Account" = Relationship(back_populates="data_grids")
    selected_filter: MuiDataGridFilter | None = Relationship(
        sa_relationship_kwargs=dict(
            lazy="selectin",
            foreign_keys="[MuiDataGrid.selected_filter_id]"
        )
    )
    filters: List[MuiDataGridFilter] = Relationship(
        cascade_delete=True,
        sa_relationship_kwargs=dict(
            back_populates="data_grid",
            foreign_keys="[MuiDataGridFilter.data_grid_id]",
        )
    )

    __table_args__ = (
        # TODO: Write unittest for postgresql_nulls_not_distinct
        sa.UniqueConstraint('settings_id', 'account_id', postgresql_nulls_not_distinct=True),
    )


class RowGroupingModel(BaseModel):
    """
    Represents the grouping configuration for rows in the MUI DataGrid
    """
    model: List[Any] = Field(default=[])


class Sorting(BaseModel):
    """
    Defines the sorting configuration, including the order of sorting for the MUI DataGrid
    """
    sortModel: List[Any] = Field(default=[])


class PaginationModel(BaseModel):
    """
    Represents the pagination settings, such as the current page and rows per page for the MUI DataGrid
    """
    page: int = Field(default=0)
    pageSize: int = Field(default=100)


class Pagination(BaseModel):
    """
    Wraps pagination metadata and model for the MUI DataGrid
    """
    meta: Dict[str, Any] = Field(default={})
    paginationModel: PaginationModel
    rowCount: int = Field(default=0)


class ColumnDimensions(BaseModel):
    """
    Defines column size constraints like width and flex for the MUI DataGrid
    """
    maxWidth: int = Field(default=-1)
    minWidth: int = Field(default=50)
    width: int | None = None
    flex: int | None = None


class Columns(BaseModel):
    """
    Encapsulates column visibility, ordering, and dimension configurations for the MUI DataGrid
    """
    columnVisibilityModel: Dict[str, bool] = Field(default={})
    orderedFields: List[str] = Field(default=[])
    dimensions: Dict[str, ColumnDimensions] = Field(default={})


class TableConfig(BaseModel):
    """
    The main configuration class for the MUI DataGrid, combining settings for grouping, sorting, pagination,
    and columns (without filters).
    """
    rowGrouping: RowGroupingModel
    pinnedColumns: Dict[str, Any] = Field(default={})
    filter: Filter
    sorting: Sorting
    density: str = Field(default="compact")
    pagination: Pagination
    columns: Columns

    @field_validator('density')
    def validate_density(cls, value):
        valid_densities = {'compact', 'standard', 'comfortable'}
        if value not in valid_densities:
            raise ValueError(f"Invalid density: {value}. Must be one of {valid_densities}")
        return value


class MuiDataGridRead(BaseModel):
    """
    Schema for reading a DataGrid configuration.
    """
    settings: Dict | None = PydanticField(default={})
