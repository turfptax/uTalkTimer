import network
import aioespnow
import asyncio
import time

class Network:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.e = aioespnow.AIOESPNow()

    def setup(self):
        self.wlan.active(True)
        self.e.active(True)
        time.sleep(1)

    async def send(self, peer, msg):
        await self.e.asend(peer, msg)

    async def receiver(self):
        async for mac, msg in self.e:
            print("Received:", msg)
            # Process the received message
            # You might want to call a callback function here
            await self.process_message(mac, msg)

    async def process_message(self, mac, msg):
        print(f"Processing message from {mac}: {msg}")
        # Add your message processing logic here

    def update(self):
        # Update network if needed
        pass
