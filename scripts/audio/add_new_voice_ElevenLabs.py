# --- Create a new IVC voice with SDK ---
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Create a voice “shell”
resp = client.voices.ivc.create(name="Yossi_Demo")  # returns voice_id
voice_id = resp.voice_id

# Optionally, add samples depends on flow (IVC may accept files at ‘add’ call via REST)
print("New voice_id:", voice_id)




"""
    --- Add a new IVC voice with audio samples via REST ---
"""


import os, requests

API_KEY = os.getenv("ELEVENLABS_API_KEY")
url = "https://api.elevenlabs.io/v1/voices/add"
headers = {"xi-api-key": API_KEY}
files = [
    ("files", ("sample1.wav", open("sample.wav","rb"), "audio/wav")),
    # add more ("files", (...)) tuples as needed
]
data = {
    "name": "Yossi_Demo",
    "description": "Consented demo voice for emergency app",
    # Optional: "labels": '{"domain":"emergency"}'
}
r = requests.post(url, headers=headers, files=files, data=data)
r.raise_for_status()
print("Created voice:", r.json())
