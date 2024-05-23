import asyncio
import websockets

from aiortc.contrib.signaling import object_from_string, object_to_string
from asyncio.exceptions import IncompleteReadError
from websockets.exceptions import ConnectionClosedError

class WebsocketSignaling:
    def __init__(self, server):
        self._server = server
        self._websocket = None
        self._reconnect_attempts = 0

    async def connect(self):
        while self._reconnect_attempts < 5:
            try:
                self._websocket = await websockets.connect(self._server)
                self._reconnect_attempts = 0 # reset attempts on success
                return
            except (ConnectionClosedError, OSError) as e:
                self._reconnect_attempts += 1
                wait_time = min(2 ** self._reconnect_attempts, 30)
                await asyncio.sleep(wait_time)

    async def close(self):
        if self._websocket is not None and self._websocket.open is True:
            await self.send(None)
            await self._websocket.close()

    async def receive(self):
        try:
            data = await self._websocket.recv()
            return object_from_string(data)
        except (ConnectionClosedError, IncompleteReadError) as e:
            self.connect()
            return None

    async def send(self, descr):
        data = object_to_string(descr)
        try:
            await self._websocket.send(data + '\n')
        except ConnectionClosedError:
            await self.connect()
