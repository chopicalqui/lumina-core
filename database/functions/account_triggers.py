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

from . import DatabaseFunction, DatabaseTrigger, TriggerEventEnum, TriggerWhenEnum, FunctionReturnEnum

__author__ = "Lukas Reiter"
__copyright__ = "Copyright (C) 2024 Lukas Reiter"
__license__ = "GPLv3"

from sqlalchemy.ext.asyncio.engine import AsyncConnection


class CleanupObsoleteAccessTokenTrigger(DatabaseFunction):
    """
    Creates database triggers and function that continuously clean up obsolete user access tokens.
    """
    def __init__(self, connection: AsyncConnection):
        super().__init__(
            connection=connection,
            name="cleanup_obsolete_access_token",
            returns=FunctionReturnEnum.trigger,
            triggers=[
                DatabaseTrigger(
                    name="on_01_account_insert",
                    table_name="accesstoken",
                    when=TriggerWhenEnum.after,
                    event=[TriggerEventEnum.insert],
                    when_clause="NEW.type = 'user'"
                )
            ]
        )

    def _create(self) -> str:
        return """
DECLARE
BEGIN
    DELETE FROM accesstoken WHERE account_id = NEW.account_id AND type = 'user' AND id <> NEW.id;
    RETURN NEW;
END;
"""
