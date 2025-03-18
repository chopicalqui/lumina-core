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

import os
import logging
import redis.asyncio as aioredis

logger = logging.getLogger("lumina.redis")


class SettingsBase:
    """
    This class manages the settings that are required by the schema.
    """
    def __init__(self):
        # Database settings
        self.db_scheme = os.getenv("DIALECT", "postgresql")
        self.db_name = os.getenv("POSTGRES_DB")
        self.db_user = os.getenv("POSTGRES_USER")
        self.db_password = os.getenv("POSTGRES_PASSWORD")
        self.db_host = os.getenv("POSTGRES_HOST")
        self.db_port = int(os.getenv("POSTGRES_PORT", 5432))
        self.db_ssl = os.getenv("POSTGRES_USE_SSL", "true").lower() == "true"
        self.db_pool_size = int(os.getenv("POSTGRES_POOL_SIZE", 10))
        self.db_max_overflow = int(os.getenv("POSTGRES_MAX_OVERFLOW", 5))
        self.db_pool_timeout = int(os.getenv("POSTGRES_POOL_TIMEOUT", 60))
        self.db_pool_recycle = int(os.getenv("POSTGRES_POOL_RECYCLE", 1800))
        self.db_pool_pre_ping = os.getenv("POSTGRES_POOL_PRE_PING", "false").lower() == "true"
        self.db_echo_pool = os.getenv("POSTGRES_ECHO_POOL")  # Set to debug to debug reset-on-return events
        self.cert = os.getenv("SSL_CERT_FILE")
        self.drop_database_objects = os.getenv("DROP_DATABASE_OBJECTS", "false").lower() == "true"
        self.create_database_objects = os.getenv("CREATE_DATABASE_OBJECTS", "false").lower() == "true"
        self.load_static_data = os.getenv("LOAD_STATIC_DATA", "false").lower() == "true"
        # Redis
        self.redis_user = os.getenv("REDIS_USER")
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.redis_host = os.getenv("REDIS_HOST")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_ssl = os.getenv("REDIS_USE_SSL", "true").lower() == "true"
        self.redis_notify_user_channel = os.getenv("REDIS_NOTIFY_USER_CHANNEL")
        # Resource files
        self.country_file = os.path.join(os.getenv("STATIC_DATA_LOCATION", ""), "country-data.json")
        # Logging
        if not self.db_host:
            raise ValueError("Database host not set.")
        if not self.db_name:
            raise ValueError("Database name not set.")
        if not self.db_user or not self.db_password:
            logger.warning("Database user or password not set.")
        if not self.redis_host:
            raise ValueError("Redis host not set.")
        if not self.db_ssl:
            logger.warning("Database is not using SSL.")
        if not self.redis_ssl:
            logger.warning("Redis is not using SSL.")

    @property
    def database_uri(self) -> str:
        uri_string = f"{self.db_scheme}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return uri_string + f"?sslmode=verify-full&sslrootcert={self.cert}" if self.db_ssl else uri_string

    async def create_redis(self, username: str | None, password: str | None) -> aioredis.Redis:
        scheme = "rediss" if self.redis_ssl else "redis"
        if username and password:
            redis_url = f"{scheme}://{self.redis_user}:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        else:
            redis_url = f"{scheme}://{self.redis_host}:{self.redis_port}"
            logger.warning("Unauthenticated access attempt to Redis.")
        return await aioredis.from_url(redis_url, decode_responses=True)
