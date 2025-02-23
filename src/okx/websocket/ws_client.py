import asyncio
import json

from websockets import connect


class OKXWebSocket:
    def __init__(self):
        self.ws_url = "wss://ws.okx.com:8443/ws/v5/public"
        self.subscriptions = []

    async def connect(self):
        self.ws = await connect(self.ws_url)
        return self.ws

    async def subscribe(self, channel, instType="SPOT"):
        msg = {"op": "subscribe", "args": [{"channel": channel, "instType": instType}]}
        await self.ws.send(json.dumps(msg))
