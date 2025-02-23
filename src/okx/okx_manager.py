from .rest.rest_client import OKXREST
from .websocket.ws_client import OKXWebSocket


class OKXManager:
    def __init__(self, api_key, api_secret, passphrase):
        self.ws_client = OKXWebSocket()
        self.rest_client = OKXREST(api_key, api_secret, passphrase)

    async def start(self):
        # WebSocket bağlantısı
        await self.ws_client.connect()

        # Tüm spot çiftleri al
        pairs = await self.get_all_pairs()

        # Tickers için subscribe
        for pair in pairs:
            await self.ws_client.subscribe("tickers", pair)

    async def get_all_pairs(self):
        # Tüm çiftleri çek
        return await self.rest_client.get_instruments("SPOT")
