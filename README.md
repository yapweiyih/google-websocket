## Summary

These two Python scripts work together to enable real-time speech recognition and audio playback using WebSockets. The first script is a WebSocket client that sends audio data from a local file to a server. The second script is a WebSocket server that receives the audio data, transcribes it using the Google Cloud Speech-to-Text API, and plays back the audio while logging the transcribed text and speech activity events. The server and client communicate using a custom protocol with events like "connected", "start", and "media" to coordinate the audio streaming and transcription process.

## Start Server

Start websocker server to keep listening to audio bytes.
```bash
python sim_server.py
```


## Start Client

Run the client to start sending audio to server.

```bash
python sim_client.py
```
