import time
import uuid

from google.cloud.dialogflowcx_v3.services.agents import AgentsClient
from google.cloud.dialogflowcx_v3.services.sessions import SessionsClient
from google.cloud.dialogflowcx_v3.types import InputAudioConfig, audio_config, session

END_OF_INPUT_TIME = None
# This math assumes LINEAR16 encoded audio
BYTES_PER_SAMPLE = 2
SAMPLE_RATE = 44100  # hertz
CHUNK_TIME = 1  # seconds per chunk
CHUNK_SIZE = int(CHUNK_TIME * SAMPLE_RATE * BYTES_PER_SAMPLE)

LOCATION = "global"
PROJECT_ID = "hello-world-418507"
RECOGNIZER = "airtel-en-in-short"
LANGUAGE = "en-US"

"""
Option 1:
    LOCATION = "global"
    AGENT_ID = "75e7c898-526d-4789-8405-b496df0bf214"

Option 2:
    LOCATION = "us-central1"
    AGENT_ID = "bf9e57c5-4518-4255-913c-e9188905d87b"
"""
LOCATION = "us-central1"
AGENT_ID = "bf9e57c5-4518-4255-913c-e9188905d87b"


def detect_intent_stream(agent, session_id, audio_file_path, language_code):
    """Returns the result of detect intent with streaming audio as input.

    Using the same `session_id` between requests allows continuation
    of the conversation."""
    session_path = f"{agent}/sessions/{session_id}"
    print(f"Session path: {session_path}\n")
    client_options = {}
    agent_components = AgentsClient.parse_agent_path(agent)
    location_id = agent_components["location"]
    if location_id != "global":
        api_endpoint = f"{location_id}-dialogflow.googleapis.com:443"
        print(f"API Endpoint: {api_endpoint}\n")
        client_options["api_endpoint"] = api_endpoint

    session_client = SessionsClient(client_options=client_options)

    input_audio_config = audio_config.InputAudioConfig(
        audio_encoding=audio_config.AudioEncoding.AUDIO_ENCODING_LINEAR_16,
        model="chirp_2",
        # sample_rate_hertz=SAMPLE_RATE,
    )

    def request_generator():
        global END_OF_INPUT_TIME
        END_OF_INPUT_TIME = None
        audio_input = session.AudioInput(config=input_audio_config)
        query_input = session.QueryInput(audio=audio_input, language_code=language_code)

        voice_selection = audio_config.VoiceSelectionParams()
        synthesize_speech_config = audio_config.SynthesizeSpeechConfig()
        output_audio_config = audio_config.OutputAudioConfig()
        # Sets the voice name and gender
        voice_selection.name = "en-GB-Standard-A"  # en-US-Neural2-A
        voice_selection.ssml_gender = (
            audio_config.SsmlVoiceGender.SSML_VOICE_GENDER_FEMALE
        )
        synthesize_speech_config.voice = voice_selection
        # Sets the audio encoding
        output_audio_config.audio_encoding = (
            audio_config.OutputAudioEncoding.OUTPUT_AUDIO_ENCODING_LINEAR_16
        )
        output_audio_config.synthesize_speech_config = synthesize_speech_config

        # The first request contains the configuration.
        yield session.StreamingDetectIntentRequest(
            session=session_path,
            query_input=query_input,
            output_audio_config=output_audio_config,
        )

        # Here we are reading small chunks of audio data from a local
        # audio file.  In practice these chunks should come from
        # an audio input device.
        with open(audio_file_path, "rb") as audio_file:
            print(f"[user starts pressing microphone]...")
            while True:
                chunk = audio_file.read(CHUNK_SIZE)
                if not chunk:
                    break
                # The later requests contains audio data.
                audio_input = session.AudioInput(audio=chunk)
                query_input = session.QueryInput(audio=audio_input)
                # simulate live microphone stream
                if END_OF_INPUT_TIME:
                    # We wanna minus of the processing time, so total add up to CHUNK_TIME
                    time.sleep(CHUNK_TIME - (time.time() - END_OF_INPUT_TIME))
                    # time.sleep(CHUNK_TIME)
                END_OF_INPUT_TIME = time.time()
                yield session.StreamingDetectIntentRequest(query_input=query_input)
                print(f"...streamed {len(chunk)} bytes")
        print(f"[user stopped pressing microphone]")

    responses = session_client.streaming_detect_intent(requests=request_generator())

    for response in responses:
        print(f'Intermediate transcript: "{response.recognition_result.transcript}".')

    # Note: The result from the last response is the final transcript along
    # with the detected content.
    response = response.detect_intent_response
    print(
        f"==\n{time.time() - END_OF_INPUT_TIME} seconds from end of input stream to final response."
    )
    print(f"Query text: {response.query_result.transcript}")
    response_messages = [
        " ".join(msg.text.text) for msg in response.query_result.response_messages
    ]
    print(f"Response text: {' '.join(response_messages)}\n")

    # The response's audio_content is binary.
    with open("output.wav", "wb") as out:
        out.write(response.output_audio)
        print('Audio content written to file "output.wav"')


if __name__ == "__main__":
    audio_file_path = "exp/audio/account_balance.wav"
    language_code = LANGUAGE
    project_id = PROJECT_ID
    location_id = LOCATION
    agent_id = AGENT_ID
    agent = f"projects/{project_id}/locations/{location_id}/agents/{agent_id}"
    print(agent)
    session_id = uuid.uuid4()

    detect_intent_stream(agent, session_id, audio_file_path, language_code)
