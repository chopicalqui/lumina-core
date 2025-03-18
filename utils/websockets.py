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
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

from .status import StatusMessage
from ..database.redis_client import notify_account
from ..models.account import Account, WebSocketNotifyAccount

logger = logging.getLogger(__name__)


class WebSocketWrapper:
    """
    This class handles the websocket connection.
    """
    def __init__(self, account: Account, websocket: WebSocket, token: str):
        self._websocket = websocket
        self._authenticated = asyncio.Event()
        self._account = Account(**account.model_dump())
        self._token = token

    async def accept(self):
        """
        Accepts the websocket connection.
        """
        await self._websocket.accept()
        logger.debug(f"Accepted websocket connection from {self._account.id}")

    async def close(self):
        """
        Closes the websocket connection.
        """
        await self._websocket.close()

    async def receive_json(self) -> Any:
        """
        Receives a JSON message from the websocket.
        """
        result = await self._websocket.receive_json()
        if self._authenticated.is_set():
            return result
        elif result.get("type") == "login" and result.get("token") == self._token:
            self._authenticated.set()
            self._token = None
            logger.debug(f"Authenticated account {self._account.id}")
            # We are using Redis to notify the account about the successful connection.
            await notify_account(
                message=WebSocketNotifyAccount(
                    account=self._account,
                    status=StatusMessage(
                        status=200,
                        message="WebSocket connection established.",
                        severity="success"
                    )
                )
            )
            return result

    async def send_json(self, message: Any):
        """
        Sends a JSON message to the websocket.
        """
        if self._authenticated.is_set() and self._websocket.state:
            try:
                await self._websocket.send_json(message)
            except RuntimeError as ex:
                logger.debug(ex)


class WebSocketManager:
    """
    This class manages the active websocket connections.
    """

    def __init__(self):
        # We maintain a list of all active connections because users can have multiple web browser tabs open.
        self.connections: Dict[str, List[WebSocketWrapper]] = {}
        self.lock = asyncio.Lock()

    async def _delete(self, account_id: str):
        """
        Closes all websocket connections.
        """
        for websocket in self.connections.get(account_id, []):
            try:
                del self.connections[account_id]
                await websocket.close()
            except Exception as ex:
                logger.debug(f"WebSocketManager._delete throw an exception: {ex}")

    async def connect(self, websocket: WebSocketWrapper, account: Account):
        """
        Connects a new websocket.
        """
        await websocket.accept()
        account_id = str(account.id)
        async with self.lock:
            if account_id not in self.connections:
                self.connections[account_id] = []
            self.connections[account_id].append(websocket)
        logger.debug(f"Connected account {account_id}")

    async def disconnect(self, account_id: str, websocket: WebSocketWrapper | None = None):
        """
        Disconnects a websocket.
        """
        async with self.lock:
            if not websocket:
                await self._delete(account_id)
            elif ((connections := self.connections[account_id]) and
                    next((conn for conn in connections if conn == websocket), None)):
                connections.remove(websocket)
                try:
                    await websocket.close()
                    logger.debug(f"Disconnected account {account_id}")
                except Exception as ex:
                    logger.debug(f"WebSocketManager._delete throw an exception: {ex}")

    async def send(self, notify: WebSocketNotifyAccount):
        """
        Sends a personal message to an account.
        """
        account_id = str(notify.account.id)
        msg = json.loads(notify.status.json())
        async with self.lock:
            for websocket in self.connections.get(account_id, []):
                try:
                    await websocket.send_json(msg)
                except Exception as ex:
                    logger.debug(f"WebSocketManager.send throw an WebSocketDisconnect exception: {ex}")
                    logger.exception(ex)
                    await self.disconnect(account_id, websocket)

    async def broadcast_json(self, message: str):
        """
        Broadcasts a message to all connected accounts.
        """
        async with self.lock:
            for account_id in self.connections:
                for websocket in self.connections.get(account_id, []):
                    try:
                        await websocket.send_json(message)
                    except Exception as ex:
                        logger.debug(f"WebSocketManager.send throw an WebSocketDisconnect exception: {ex}")
                        logger.exception(ex)
                        await self.disconnect(account_id, websocket)


manager = WebSocketManager()
