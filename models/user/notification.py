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
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Column, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects import postgresql


class Notification(SQLModel, table=True):
    """
    Store information about a user's notifications.
    """
    __tablename__ = "user_notification"
    id: UUID = Field(
        primary_key=True,
        index=True,
        sa_column_kwargs=dict(server_default=func.gen_random_uuid()),
        description="The unique identifier of the token."
    )
    subject: str = Field(description="The subject of the notification.")
    message: str = Field(description="The message of the notification.")
    read: bool = Field(
        sa_column_kwargs=dict(server_default='false'),
        description="Indicates if the notification has been read."
    )
    # Internal information only
    created_at: datetime = Field(
        sa_column_kwargs=dict(server_default=func.now()),
        description="The date and time when the token was created."
    )
    last_modified_at: datetime | None = Field(
        default=None,
        sa_column_kwargs=dict(onupdate=func.now()),
        description="The date and time when the token was last modified."
    )
    # Foreign keys
    user_id: UUID = Field(
        default=None,
        sa_column=Column(postgresql.UUID(as_uuid=True), ForeignKey("user_data.id", ondelete="CASCADE")),
        description="Foreign key to the user that the notification belongs to."
    )


class NotificationRead(BaseModel):
    """
    This is the notification schema. It is used by the FastAPI to read a notification.
    """
    id: UUID
    subject: str
    message: str
    read: bool
    created_at: datetime
