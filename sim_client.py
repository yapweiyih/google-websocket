import asyncio
import json
import wave
from time import sleep

import websockets
from loguru import logger

# WebSocket server address
SERVER_ADDRESS = "ws://localhost:8765"

# Audio file path
AUDIO_FILE = "../exp/audio/account_balance.wav"

# Chunk size in bytes
CHUNK_SIZE = 20000

# Event types
EVENT_TYPE_CONNECTED = "connected"
EVENT_TYPE_START = "start"
EVENT_TYPE_MEDIA = "media"


# WebSocket client handler
async def client_handler():
    async with websockets.connect(SERVER_ADDRESS) as websocket:
        # Send the "connected" event
        connected_event = json.dumps({"type": EVENT_TYPE_CONNECTED})
        await websocket.send(connected_event)
        logger.info("Sent 'connected' event")

        # Wait for the "start" event from the server
        start_event = await websocket.recv()
        logger.info(f"Received: {start_event}")

        # Open the audio file
        with wave.open(AUDIO_FILE, "rb") as wav:
            logger.info("Opening audio file...")
            audio_data = wav.readframes(wav.getnframes())

            # Send the "start" event
            start_event = json.dumps({"type": EVENT_TYPE_START})
            logger.info("Sent 'start' event")
            await websocket.send(start_event)

            # Break the audio data into chunks and send them as "media" events
            for i in range(0, len(audio_data), CHUNK_SIZE):
                chunk = audio_data[i : i + CHUNK_SIZE]
                import base64

                encoded_chunk = base64.b64encode(chunk).decode("utf-8")
                media_event = json.dumps(
                    {"type": EVENT_TYPE_MEDIA, "data": encoded_chunk}
                )
                await websocket.send(media_event)
                logger.info(f"Sent media chunk ({len(chunk)} bytes)")
                sleep(0.1)


# Run the WebSocket client
asyncio.get_event_loop().run_until_complete(client_handler())
