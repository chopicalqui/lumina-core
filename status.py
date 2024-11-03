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
from enum import IntEnum, auto
from typing import Any, Dict
from pydantic import BaseModel, Field as PydanticField, ConfigDict, field_validator


class SeverityEnum(IntEnum):
    """
    Enum that defines MUI's Alert severity levels.
    """
    error = auto()
    success = auto()
    info = auto()
    warning = auto()


class StatusMessage(BaseModel):
    """
    Status message that is used to send status information to the frontend.
    """
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=False,  # Ensure that enum values are not automatically used
        json_encoders={SeverityEnum: lambda x: x.name}
    )
    status: int
    severity: SeverityEnum
    message: str
    open: bool = PydanticField(default=True)
    error_code: UUID | None = PydanticField(default=None)
    payload: Dict[str, Any] | None = PydanticField(default=None)

    @field_validator('severity', mode='before')
    def convert_int_serial(cls, v):
        if isinstance(v, str):
            v = SeverityEnum[v]
        return v
