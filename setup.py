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


from sqlmodel import SQLModel
from sqlalchemy.future import select
from .database import engine, async_session, settings_base as settings
# We need to import all models to ensure they are created.
from .models.user.user import User
from .models.country import Country


async def drop_db_and_tables():
    """
    Drops all items in the database.
    """
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def create_db_and_tables():
    """
    Create all items in the database.
    """
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def import_countries():
    """
    Import all countries from the countries.json file.
    """
    import json
    async with async_session() as session:
        with open(settings.country_file, "r") as file:
            for item in json.load(file):
                country = Country(**item)
                result = await session.execute(
                    select(Country).filter_by(code=country.code)
                )
                if not result.scalars().first():
                    session.add(country)
            await session.commit()


async def init_db(
        drop_tables: bool = False,
        create_tables: bool = False,
        load_data: bool = False
):
    """
    Initializes the database.
    """
    if drop_tables:
        await drop_db_and_tables()
    if create_tables:
        await create_db_and_tables()
    if load_data:
        # Initialize static lookup tables
        await import_countries()
