import asyncio
from aiortc.contrib.signaling import RTCSessionDescription, RTCIceCandidate, candidate_from_sdp, candidate_to_sdp
import json

from . import aes
from .app import App
from socketio import AsyncClient
from socketio.exceptions import TimeoutError, ConnectionError

class SecureputSignaling():
    _sio = AsyncClient()
    _connected = False
    _handle_signal = None

    def __init__(self, server, identity_file, name, metadata={}):
        self._app = App(identity_file, name)
        self._server = server
        self._metadata = metadata
        self._sio.on('message', self.on_message)
        self._sio.on('connect', self.on_connect)
        self._sio.on('connect_error', self.on_connect_error)
        self._sio.on('disconnect', self.on_disconnect)

    def set_signaling_handler(self, handler):
        self._handle_signal = handler

    async def on_connect(self):
        print("I'm connected!")
        await self.sendIdentity()

    def on_connect_error(self, data):
        print("The connection failed!")

    def on_disconnect(self):
        print("I'm disconnected!")

    async def on_message(self, data):
        print("received message", data)
        obj = await self.parse_message(data)
        if self._handle_signal:
            await self._handle_signal(obj)

    async def parse_message(self, data):
        ret = self.json_to_object(data)
        if ret == None:
            print("remote host says good bye!")
        elif isinstance(ret, dict):
            if ret['type'] == 'claim':
                await self.claim(ret['payload']['account'])
            else:
                if ret["type"] == "SessionDescription":
                    sdp = ret["payload"]["sdp"]
                    type = ret["payload"]["type"]
                    return RTCSessionDescription(sdp=sdp, type=type)
                elif ret["type"] == "IceCandidate":
                    candidate = candidate_from_sdp(ret["payload"]["sdp"].split(":", 1)[1])
                    candidate.sdpMid = ret["payload"]["sdpMid"]
                    candidate.sdpMLineIndex = ret["payload"]["sdpMLineIndex"]
                    return candidate
        return ret

    async def connect(self):
        while self._connected == False:
            try:
                print("connecting to %s" % self._server)
                await self._sio.connect(self._server)
                self._connected = True
                if not self._app.paired():
                    self._app.gen_pair_info()
                await self._sio.wait()
            except ConnectionError as e:
                print("connection error", e)
                await asyncio.sleep(1)

    def decrypt(self, data):
        return aes.decrypt(self._app.config["deviceSecret"], data)

    def json_to_object(self, message_str):
        message = json.loads(message_str)

        if message["type"] == "wrapped":
            message = json.loads(aes.decrypt(self._app.config["deviceSecret"], message["payload"]["data"]))

        return message

    def object_to_json(self, obj):
        if isinstance(obj, RTCSessionDescription):
            message = self.forwardWrap({
                "type": "SessionDescription",
                "payload": {"sdp": obj.sdp, "type": obj.type}
            })
        elif isinstance(obj, RTCIceCandidate):
            message = self.forwardWrap({
                "type": "IceCandidate",
                "payload": {
                    "sdp": "candidate:" + candidate_to_sdp(obj),
                    "sdpMid": obj.sdpMid,
                    "sdpMLineIndex": obj.sdpMLineIndex,
                }
            })
        else:
            message = obj

        return message

    async def send(self, descr):
        data = self.object_to_json(descr)
        await self._sio.emit('message', data)

    async def sendIdentity(self):
        await self.send(json.dumps({
            "type": "identify-target",
            "payload": {
                "name": self._app.config["deviceName"],
                "device": self._app.config["deviceUUID"],
                "account": self._app.config["accountUUID"],
                "metadata": self._metadata
            }
        }))

    async def claim(self, account):
        self._app.config["accountUUID"] = account
        print("claimed to account %s" % account)
        await self.sendIdentity()

    def forwardWrap(self, json_data: dict) -> str:
        msg = {
            'to': self._app.config["accountUUID"],
            'type': 'forward-wrapped',
        }
        # Encrypt the plaintext
        ciphertext = aes.encrypt(self._app.config["deviceSecret"], json.dumps(json_data))
        
        # Install the ciphertext into the payload
        msg['body'] = ciphertext
        
        return msg
