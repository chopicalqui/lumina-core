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
    filters: List["MuiDataGridFilter"] = Relationship(back_populates="data_grid")

    __table_args__ = (
        # TODO: Write unittest for postgresql_nulls_not_distinct
        sa.UniqueConstraint('settings_id', 'account_id', postgresql_nulls_not_distinct=True),
    )


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


class RowGroupingModel(BaseModel):
    """
    Represents the grouping configuration for rows in the MUI DataGrid
    """
    model: List[Any] = Field(default=[])


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
    The main configuration class for the MUI DataGrid, combining settings for grouping, filtering, sorting, pagination, and columns
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
