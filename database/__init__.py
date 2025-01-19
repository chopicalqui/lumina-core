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

from abc import abstractmethod
from uuid import UUID
from typing import Any, Type, List
from pydantic import BaseModel
from sqlmodel import SQLModel
from sqlalchemy import UniqueConstraint, text
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.engine import AsyncConnection

from ..utils import NotFoundError
from ..utils.config import SettingsBase

# This is a workaround to add the NULLS NOT DISTINCT option to the UNIQUE constraint.
# Source: https://stackoverflow.com/questions/57646553/treating-null-as-a-distinct-value-in-a-table-unique-constraint
UniqueConstraint.argument_for("postgresql", 'nulls_not_distinct', None)


class DatabaseObjectBase:
    """
    Base class for managing database objects like views, procedures and triggers.
    """
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    async def _execute(self, content: str):
        """
        Executes the given SQL statement.
        """
        # print(content)
        await self._connection.execute(text(content).execution_options(autocommit=True))

    @abstractmethod
    async def create(self, **kwargs):
        """
        Create the database object.
        """
        ...

    @abstractmethod
    async def drop(self, **kwargs):
        """
        Drop the database object.
        """
        ...


@compiles(UniqueConstraint, "postgresql")
def compile_create_uc(create, compiler, **kw):
    """Add NULLS NOT DISTINCT if its in args."""
    stmt = compiler.visit_unique_constraint(create, **kw)
    postgresql_opts = create.dialect_options["postgresql"]

    if postgresql_opts.get("nulls_not_distinct"):
        return stmt.rstrip().replace("UNIQUE (", "UNIQUE NULLS NOT DISTINCT (")
    return stmt


async def get_by_id(session: AsyncSession, model: Type, item_id: UUID, inloadlist: List[Any] = None) -> Any:
    """
    Get an object of class model by its ID from the database.
    """
    # Create initial query
    query = select(model).where(model.id == item_id)
    # Side-load additional relationship data that needs to be updated
    for relationship in (inloadlist or []):
        query = query.options(selectinload(relationship))
    if not (result := (await session.execute(query)).scalar_one_or_none()):
        raise NotFoundError(f"{model.__name__} with ID '{item_id}' not found.")
    return result


async def update_database_record(
        session: AsyncSession,
        source: BaseModel,
        query_model: Type[BaseModel],
        source_model: Type[BaseModel],
        commit: bool,
        inloadlist: List[Any] = None,
        **kwargs
) -> SQLModel:
    """
    Updates the database record with the given source object.
    :param session: The database session used to update the record.
    :param source: The source object that contains the new values. The source's ID is used to identify the record in the
        database.
    :param query_model: The class of the object that is queried from the database.
    :param source_model: The class of the source object.
    :param commit: If True, the changes are committed to the database.
    :param inloadlist: A list of relationships that are side-loaded when the object is queried from the database.
    :param kwargs: Additional keyword arguments that are passed to the update_attributes method.
    :return:
    """
    result = await get_by_id(session=session, model=query_model, item_id=source.id, inloadlist=inloadlist)
    update_attributes(target=result, source=source, source_model=source_model, **kwargs)
    session.add(result)
    if commit:
        await session.commit()
        await session.refresh(result)
    return result


def update_attributes(
        target: SQLModel,
        source: BaseModel,
        source_model: Type[BaseModel],
        **kwargs
):
    """
    Updates the attributes of the target object with the attributes of the source object.
    :param target: The target object that is updated.
    :param source: The source object that contains the new values.
    :param source_model: The class of the source object.
    :param kwargs: Additional keyword arguments that are passed to the Pydantic model_dump method of the source object.
    :return:
    """
    # First, we create a temporary object that contains the new values. This allows us to apply all necessary
    # transformations using the Pydantic model_dump method.
    tmp = source_model(**source.model_dump(**kwargs)).model_dump(**kwargs)
    for key, value in tmp.items():
        if hasattr(target, key):
            setattr(target, key, value)
    return target


settings_base = SettingsBase()
engine = create_async_engine(
    settings_base.database_uri,
    pool_size=settings_base.db_pool_size,
    max_overflow=settings_base.db_max_overflow,
    pool_timeout=settings_base.db_pool_timeout,
    pool_recycle=settings_base.db_pool_recycle,
    echo_pool=settings_base.db_echo_pool,
    pool_pre_ping=settings_base.db_pool_pre_ping
)
async_session = async_sessionmaker(engine, autoflush=False, autocommit=False, expire_on_commit=False)


async def get_db():
    """
    Dependency to allow FastAPI endpoints to access the database.
    """
    db = async_session()
    try:
        yield db
    finally:
        await db.close()
