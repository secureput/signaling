import asyncio
import websockets

from aiortc.contrib.signaling import object_from_string, object_to_string
from asyncio.exceptions import IncompleteReadError
from websockets.exceptions import ConnectionClosedError

class WebsocketSignaling:
    def __init__(self, server):
        self._server = server
        self._websocket = None

    async def connect(self):
        self._websocket = None
        while self._websocket == None:
            try:
                print("Connecting websocket...")
                self._websocket = await websockets.connect(self._server)
                return
            except (ConnectionClosedError, OSError) as e:
                print("Websocket connection error, retrying soon", e)
                await asyncio.sleep(1)
        print("Websocket connected")

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
