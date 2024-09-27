import asyncio
import base64
import json
import queue
import threading
import wave
from time import sleep
from typing import Iterator

import pyaudio
import websockets
from google.api_core.client_options import ClientOptions
from google.cloud import speech_v2
from google.cloud.speech_v2 import types
from loguru import logger

LOCATION = "asia-south1"
PROJECT_ID = "hello-world-418507"
RECOGNIZER = "airtel-en-in-short"
SAMPLE_RATE = 44100

speech_client = speech_v2.SpeechClient(
    client_options=ClientOptions(
        api_endpoint=f"{LOCATION}-speech.googleapis.com",
    )
)

media_queue = queue.Queue()


def transcript_thread(audio_queue):
    logger.info("Starting stt thread")

    recognition_config = types.RecognitionConfig(
        explicit_decoding_config=types.ExplicitDecodingConfig(
            encoding=types.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            audio_channel_count=1,
        ),
        language_codes=["en-US"],
        model="long",
    )
    # Sets the flag to enable voice activity events
    streaming_features = types.StreamingRecognitionFeatures(
        enable_voice_activity_events=True
    )
    streaming_config = types.StreamingRecognitionConfig(
        config=recognition_config, streaming_features=streaming_features
    )

    config_request = types.StreamingRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/{LOCATION}/recognizers/_",
        streaming_config=streaming_config,
    )

    # Transcribes the audio into text
    responses_iterator = speech_client.streaming_recognize(
        requests=create_requests(config_request, audio_queue),
    )
    responses = []
    logger.info("Starting transcripting")

    for response in responses_iterator:
        responses.append(response)
        if (
            response.speech_event_type
            == types.StreamingRecognizeResponse.SpeechEventType.SPEECH_ACTIVITY_BEGIN
        ):
            logger.info("Speech started.")
        if (
            response.speech_event_type
            == types.StreamingRecognizeResponse.SpeechEventType.SPEECH_ACTIVITY_END
        ):
            logger.info("Speech ended.")
        for result in response.results:
            logger.info(f"Transcript: {result.alternatives[0].transcript}")


def create_requests(config, audio_queue):
    logger.info("Creating requests")
    yield config
    while True:
        try:
            logger.info("Getting audio from queue")
            yield types.StreamingRecognizeRequest(
                audio=audio_queue.get(timeout=0.5)
            )  # Client should send faster than this timeout
        except queue.Empty:
            logger.info("Audio queue is empty")
            return
        except Exception as e:
            logger.error(e)


def play_audio_thread(q):
    logger.info("Starting audio playback thread")
    audio = pyaudio.PyAudio()

    # Open a stream to play the audio
    stream = audio.open(
        format=audio.get_format_from_width(2),
        channels=1,
        rate=SAMPLE_RATE,
        output=True,
    )

    while True:
        try:
            media_data = q.get(timeout=1)
            # logger.info("Taking out audio chunk")

            stream.write(media_data)
        except queue.Empty:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            logger.info("Audio playback closed.")
            pass


# Define the WebSocket server handler
async def handler(websocket, path):
    # Get the client's IP address
    client_ip = websocket.remote_address[0]
    logger.info("*" * 50)
    logger.info(f"Client connected from {client_ip}")

    # Start the audio playback thread
    audio_thread = threading.Thread(target=transcript_thread, args=(media_queue,))
    audio_thread.daemon = (
        True  # Allow main thread to exit even if audio thread is running
    )
    audio_thread.start()

    try:
        logger.info("try catch..")
        audio = pyaudio.PyAudio()

        # Open a stream to play the audio
        stream = audio.open(
            format=audio.get_format_from_width(2),
            channels=1,
            rate=SAMPLE_RATE,
            output=True,
        )
        async for event in websocket:
            await websocket.send("Connected to server successfully.")

            try:
                # Attempt to parse the event data as JSON
                event_json = json.loads(event)
                event_type = event_json.get("type")

                # Handle different event types
                if event_type == "connected":
                    logger.info("IQ is connected")

                elif event_type == "start":
                    logger.info("Processing 'start' event")

                elif event_type == "media":
                    # logger.info("Received media data")
                    media_data_base64 = event_json["data"]
                    media_data = base64.b64decode(media_data_base64)
                    media_queue.put(media_data)

                    # logger.info("Playing audio...")
                    # stream.write(media_data)

            except (json.JSONDecodeError, KeyError):
                logger.info("Invalid event data format")

        stream.stop_stream()
        stream.close()
        audio.terminate()
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed by client {client_ip}")


# Start the WebSocket server
start_server = websockets.serve(handler, "localhost", 8765)

# Run the server
logger.info("WebSocket server started on localhost:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
