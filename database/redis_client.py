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

import json
import time
import logging
from redis.exceptions import ConnectionError
from typing import Dict, Callable, Coroutine
from . import settings_base
from ..utils import LuminaError
from core.models.account import WebSocketNotifyAccount as NotifyAccount

logger = logging.getLogger(__name__)


class RedisConnectionError(LuminaError):
    """
    Raised when connecting to Redis failed.
    """
    def __init__(self, message: str | None = "Connection to Redis failed."):
        super().__init__(message)
        self.status_code = 500


async def publish(
        username: str,
        password: str,
        channel: str,
        message: str | Dict
):
    """
    Sends a message to the given message broker's channel.

    :param username: The username for the Redis server.
    :param password: The password for the Redis server.
    :param channel: The channel to which the caller wants to send the message.
    :param message: The message that shall be published.
    """
    r = await settings_base.create_redis(username=username, password=password)
    try:
        result = json.dumps(message) if isinstance(message, dict) else message
        await r.lpush(channel, result)
        logger.debug(f"Published message to channel {channel}.")
    except ConnectionError as e:
        logger.exception(e)
    finally:
        await r.aclose()


async def subscribe(
        username: str,
        password: str,
        channel: str,
        callback: Callable[[str], Coroutine]
):
    """
    Subscribes to the given message broker's channel and calls the callback function for each message.

    :param username: The username for the Redis server.
    :param password: The password for the Redis server.
    :param channel: The channel to which the caller wants to subscribe.
    :param callback: The function that shall be called for each message.
    """
    r = settings_base.create_redis(username=username, password=password)
    while True:
        try:
            message = await r.blpop(channel)
            chl, data = message
            if data is not None and chl.decode() == channel:
                logger.debug(f"Received message from channel {channel}.")
                await callback(data.decode())
        except ConnectionError:
            logger.warning("Lost connection to Redis. Reconnecting in 10 seconds ...")
            time.sleep(10)


async def notify_user(
        message: NotifyAccount,
):
    """
    Sends a message to the given user via Redis and WebSockets.
    """
    await publish(
        username=settings_base.redis_user,
        password=settings_base.redis_password,
        channel=settings_base.redis_notify_user_channel,
        message=message.json()
    )
