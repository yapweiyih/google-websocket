import asyncio
import json

import websockets


class Client:
    def __init__(
        self,
        url="ws://localhost:8000",
    ):  # Changed the URL to localhost:8000
        self.url = url
        self.ws = None

    def log(self, *args):
        print(*args)

    async def connect(self, model="dummy"):  # Changed the model parameter
        if self.is_connected():
            raise Exception("Already connected")
        self.ws = await websockets.connect(self.url)
        self.log(f"Connected to {self.url}")
        self.receive_task = asyncio.create_task(self._receive_messages())

    def is_connected(self):
        return self.ws is not None and not self.ws.closed

    async def _receive_messages(self):
        async for message in self.ws:
            self.log(message)


# Example usage
async def main():
    client = Client()
    await client.connect()
    # Add your code here to interact with the dummy server
    await client.receive_task


if __name__ == "__main__":
    asyncio.run(main())
