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

from sqlalchemy.engine import Connection
from .. import DatabaseObjectBase


class DatabaseView(DatabaseObjectBase):
    """
    Base class to manage database triggers
    """
    def __init__(
            self,
            connection: Connection,
            name: str,
            query: str
    ):
        super().__init__(connection)
        self.name = name
        self.query = query

    def create(self):
        self._execute(f"CREATE OR REPLACE VIEW {self.name} AS {self.query}")

    def drop(self):
        self._execute(f"DROP VIEW IF EXISTS {self.name}")
