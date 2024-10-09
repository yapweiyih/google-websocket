import asyncio


class EventEmitter:
    def __init__(self):
        self.handlers = {}

    def on(self, event_name, handler):
        if event_name not in self.handlers:
            self.handlers[event_name] = []
        self.handlers[event_name].append(handler)

    def emit(self, event_name, event):
        if event_name in self.handlers:
            for handler in self.handlers[event_name]:
                handler(event)

    async def wait_for_next(self, event_name):
        future = asyncio.Future()

        def handler(event):
            if not future.done():
                future.set_result(event)

        self.on(event_name, handler)
        return await future


async def main():
    emitter = EventEmitter()

    # Wait for the 'data' event
    print('Waiting for "data" event...')
    data_future = asyncio.create_task(emitter.wait_for_next("data"))

    # Wait for the 'error' event
    print('Waiting for "error" event...')
    error_future = asyncio.create_task(emitter.wait_for_next("error"))

    # Emit events after a short delay
    await asyncio.sleep(1)
    emitter.emit("data", "Hello, World!")
    await asyncio.sleep(1)
    emitter.emit("error", "Something went wrong!")

    # Get the results of the futures
    data = await data_future
    error = await error_future

    print(f"Received data: {data}")
    print(f"Received error: {error}")


asyncio.run(main())
