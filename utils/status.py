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

from enum import StrEnum
from typing import Any, Dict
from pydantic import BaseModel, Field as PydanticField, ConfigDict


class AlertSeverityEnum(StrEnum):
    """
    Enum that defines MUI's Alert severity levels.
    """
    error = "error"
    success = "success"
    info = "info"
    warning = "warning"


class StatusMessage(BaseModel):
    """
    Status message that is used to send status information to the frontend.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={AlertSeverityEnum: lambda x: x.name}
    )
    type: str = "statusMessage"
    status: int
    severity: AlertSeverityEnum
    message: str
    payload: Dict[str, Any] | None = PydanticField(default=None)
