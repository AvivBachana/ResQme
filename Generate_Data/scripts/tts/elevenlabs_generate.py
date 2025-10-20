from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv


import csv

# from scripts.audio.add_new_voice_ElevenLabs import voice_id

load_dotenv()

# Read from the input CSV
input_file = '/Generate_Data/src/resqme/data/text/generated_gpt_calls.csv'
output_file = 'output.csv'


elevenlabs = ElevenLabs(
  api_key="sk_8584e8ea1b5ce37d0cfedd6b4509e02121d9f3508fe1f88d",
)

# def initialize_elevenlabs():
#     global elevenlabs
#     elevenlabs = ElevenLabs(
#       api_key=os.getenv("ELEVENLABS_API_KEY"),
#     )

VOICES_LIST = ["OLMZ4YtF8AcDL7aQQMcp"]

def process_row(enum, row, voice_id):
    """Process a single row and generate audio"""
    try:
        if len(row) != 3:
            print(f"✗ Skipping row {enum + 1}: expected 3 columns, got {len(row)} → {row}")
            return enum, False

        audio = elevenlabs.text_to_speech.convert(
            text=row[2],
            voice_id=voice_id,
            model_id="eleven_v3",
            output_format="mp3_44100_128",
        )

        filename = f"audio_{enum+1}.mp3"
        with open(filename, "wb") as f:
            f.write(b"".join(audio))
        print(f"✓ Generated {filename}")
        return enum, True
    except Exception as e:
        print(f"✗ Error processing row {enum+1}: {e}")
        return enum, False

# Read and write the CSV data
with open(input_file, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    rows = list(reader)
    
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        
        # Process rows in parallel using up to 3 threads
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for enum, row in enumerate(rows):
                if enum == 0:
                    continue
                future = executor.submit(process_row, enum, row,voice_id= VOICES_LIST[enum % len(VOICES_LIST)])
                futures.append(future)
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                enum, success = future.result()

print(f"Successfully processed data from {input_file}")