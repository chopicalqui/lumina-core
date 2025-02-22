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

from enum import Enum
from typing import List, Optional
from abc import abstractmethod
from sqlalchemy.ext.asyncio.engine import AsyncConnection

from .. import DatabaseObjectBase


class TriggerWhenEnum(Enum):
    before = "BEFORE"
    after = "AFTER"
    instead_of = "INSTEAD OF"


class TriggerEventEnum(Enum):
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"
    truncate = "TRUNCATE"


class FunctionReturnEnum(Enum):
    void = "VOID"
    trigger = "TRIGGER"
    anyelement = "ANYELEMENT"


class DatabaseTrigger:
    """
    Base class to manage database triggers
    """

    def __init__(
            self,
            name: str,
            table_name: str,
            when: TriggerWhenEnum,
            event: List[TriggerEventEnum],
            when_clause: Optional[str] = None
    ):
        if len(event) == 0:
            raise ValueError("The event argument must contain at least one element.")
        self.name = name
        self._table_name = table_name
        self._when = when
        self._event = event
        self._when_clause = when_clause

    def create(self, function_name: str) -> str:
        """
        Creates the database trigger.
        """
        events = [item.value for item in self._event]
        when_clause = f"WHEN ({self._when_clause})" if self._when_clause else ""
        if len(events) == 0:
            raise ValueError("The event argument must contain at least one element.")
        elif len(events) == 1:
            event_text = events[0]
        elif len(events) == 2:
            event_text = " OR ".join(events)
        else:
            event_text = " ".join(events[:-1]) + " OR " + events[-1]
        return f"CREATE OR REPLACE TRIGGER {self.name} {self._when.value} {event_text} ON {self._table_name} FOR EACH ROW {when_clause} EXECUTE PROCEDURE {function_name}();"

    def drop(self) -> str:
        return "DROP TRIGGER IF EXISTS " + self.name + " ON " + self._table_name + ";"


class FunctionArgument:
    def __init__(self, name: str, argument_type: str):
        self.name = name
        self.type = argument_type


class DatabaseFunction(DatabaseObjectBase):
    """
    Base class to manage database triggers
    """

    def __init__(
            self,
            connection: AsyncConnection,
            name: str,
            returns: FunctionReturnEnum,
            arguments: List[FunctionArgument] = None,
            triggers: List[DatabaseTrigger] = None
    ):
        super().__init__(connection)
        self._triggers = triggers if triggers else []
        if len(set([item.name for item in self._triggers])) != len(self._triggers):
            raise ValueError("The trigger names must be unique!")
        self.name = name
        self._returns = returns
        self._arguments = ", ".join([f"{item.name} {item.type}" for item in (arguments if arguments else [])])

    async def drop(self):
        """
        Drop the function together with all calling triggers.
        """
        # Drop all database triggers
        for trigger in self._triggers:
            await self._execute(trigger.drop())
        # Drop the function
        await self._execute("DROP FUNCTION IF EXISTS " + self.name + ";")

    async def create(self):
        """
        Create the function together with all calling triggers.
        """
        body = self._create().strip()
        content = f"""CREATE OR REPLACE FUNCTION {self.name}({self._arguments})
RETURNS {self._returns.name.upper()} AS $$
{body}
$$ LANGUAGE PLPGSQL;"""
        # Create the function
        await self._execute(content)
        # Create the database triggers calling this function
        for trigger in self._triggers:
            await self._execute(trigger.create(self.name))

    @abstractmethod
    def _create(self) -> str:
        """
        Creates the PostgreSQL function.
        """
        ...
