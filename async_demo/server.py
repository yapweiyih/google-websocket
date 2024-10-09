import asyncio

import websockets

# List to store connected clients
connected_clients = []


async def send_message(message, websocket):
    try:
        await websocket.send(message)
    except websockets.exceptions.ConnectionClosedError:
        # Remove the disconnected client from the list
        connected_clients.remove(websocket)


async def broadcast_message(message):
    # Send the message to all connected clients
    await asyncio.gather(
        *[send_message(message, websocket) for websocket in connected_clients]
    )


async def handle_client(websocket, path):
    # Add the new client to the list
    connected_clients.append(websocket)
    print(f"New client connected: {websocket.remote_address}")
    counter = 0
    try:
        while True:
            # Send "harlo" every 5 seconds
            await broadcast_message(str(counter))
            await asyncio.sleep(1)
            counter += 1
    finally:
        # Remove the disconnected client from the list
        connected_clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")


async def main():
    server = await websockets.serve(handle_client, "localhost", 8000)
    print("Server started at ws://localhost:8000")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
