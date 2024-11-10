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

from .views.util import create_views, drop_views
from .functions.util import create_functions, drop_functions


async def setup(drop: bool = False, create: bool = False):
    """
    Set up the database objects.
    """
    if drop:
        await drop_views()
        await drop_functions()
    if create:
        await create_functions()
        await create_views()
