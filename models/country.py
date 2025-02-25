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

import uuid
import sqlalchemy as sa
from sqlalchemy.sql import func
from datetime import datetime
from sqlmodel import Field, SQLModel
from pydantic import BaseModel, Field as PydanticField, AliasChoices


class Country(SQLModel, table=True):
    """
    Store and manage location information.
    """
    id: uuid.UUID = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs=dict(server_default=func.gen_random_uuid()),
        description="The unique identifier of the country."
    )
    name: str = Field(unique=True, description="The name of the country.")
    code: str = Field(unique=True, description="The code of the country.")
    phone: str = Field(description="The phone code of the country.")
    default: bool = Field(
        sa_column_kwargs=dict(server_default='false'),
        description="Countries marked as default are displayed first."
    )
    display: bool = Field(
        sa_column_kwargs=dict(server_default='true'),
        description="Defines whether the country should be returned by the backend."
    )
    svg_image: str = Field(description="The SVG image of the country.")
    # Internal information only
    created_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        description="The date and time when the country was created."
    )
    last_modified_at: datetime | None = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        description="The date and time when the country was last modified."
    )


class CountryLoad(BaseModel):
    """
    This is the country schema for loading data from the file system.
    """
    code: str
    name: str
    phone: str
    svg_image: str


class CountryRead(SQLModel):
    """
    This is the country schema. It is used by the FastAPI to return information about a country.
    """
    id: uuid.UUID
    name: str
    code: str
    phone: str
    default: bool
    display: bool


class CountryUpdate(SQLModel):
    """
    This is the country schema. It is used by the FastAPI to update information about a country.
    """
    id: uuid.UUID
    default: bool
    display: bool


class CountryLookup(BaseModel):
    """
    This is the country lookup schema. It is used by the FastAPI to return information about a country.
    """
    id: uuid.UUID
    name: str = PydanticField(serialization_alias="label")
    code: str = PydanticField()
