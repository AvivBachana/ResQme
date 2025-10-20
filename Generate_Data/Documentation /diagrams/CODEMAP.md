# Code Map for `ResQme`

## Directory Tree

```
ResQme
├── notebooks
│   ├── demo_pipeline.ipynb
│   └── EDA.ipynb
├── scripts
│   ├── audio
│   │   ├── add_new_voice_ElevenLabs.py
│   │   ├── add_noise.py
│   │   └── preprocess_audio.py
│   ├── eval
│   │   └── evaluate_baseline.py
│   ├── llm
│   │   ├── generate_with_openai.py
│   │   └── generate_with_tinyllama.py
│   ├── train
│   │   └── train_baseline.py
│   ├── tts
│   │   ├── tts_elevenlabs.py
│   │   └── tts_google.py
│   └── utils
│       └── cli.py
├── src
│   └── resqme
│       ├── data
│       │   ├── processed
│       │   │   └── generated_gpt_calls.csv
│       │   └── raw
│       │       └── disease_symptom_matrix.csv
│       ├── pipelines
│       │   ├── audio
│       │   │   ├── audio_preprocess.py
│       │   │   └── audio_utils.py
│       │   ├── llm
│       │   │   ├── data_adapter.py
│       │   │   ├── generate_monologues.py
│       │   │   ├── openai_adapter.py
│       │   │   └── tinyllama_adapter.py
│       │   └── tts
│       │       ├── ElevenLabsTTS.py
│       │       └── tts_adapter.py
│       ├── __init__.py
│       └── config.py
├── tests
│   └── test_monologue_gen.py
├── keys.json
├── Makefile
├── README.md
└── requirements.txt
```

## Modules

### scripts.audio.add_new_voice_ElevenLabs

**File:** `scripts/audio/add_new_voice_ElevenLabs.py`

**Imports:** elevenlabs, os, requests

**Module docstring / summary:**

_No module docstring found._

### scripts.audio.add_noise

**File:** `scripts/audio/add_noise.py`

**Imports:** glob, os, src.resqme.pipelines.audio.audio_utils

**Module docstring / summary:**

_No module docstring found._

### scripts.audio.preprocess_audio

**File:** `scripts/audio/preprocess_audio.py`

**Imports:** glob, os, src.resqme.pipelines.audio.audio_preprocess

**Module docstring / summary:**

_No module docstring found._

### scripts.eval.evaluate_baseline

**File:** `scripts/eval/evaluate_baseline.py`

**Imports:** json, os

**Module docstring / summary:**

_No module docstring found._

**Functions:** evaluate_baseline

### scripts.llm.generate_with_openai

**File:** `scripts/llm/generate_with_openai.py`

**Imports:** src.resqme.pipelines.llm.openai_adapter

**Module docstring / summary:**

_No module docstring found._

### scripts.llm.generate_with_tinyllama

**File:** `scripts/llm/generate_with_tinyllama.py`

**Imports:** src.resqme.pipelines.llm.tinyllama_adapter

**Module docstring / summary:**

_No module docstring found._

### scripts.train.train_baseline

**File:** `scripts/train/train_baseline.py`

**Imports:** os

**Module docstring / summary:**

_No module docstring found._

**Functions:** train_baseline

### scripts.tts.tts_elevenlabs

**File:** `scripts/tts/tts_elevenlabs.py`

**Imports:** ResQme.src.resqme.pipelines.tts.ElevenLabsTTS, argparse, pathlib

**Module docstring / summary:**

CLI script for ElevenLabs TTS.

**Functions:** main

### scripts.tts.tts_google

**File:** `scripts/tts/tts_google.py`

**Imports:** src.resqme.pipelines.tts.tts_adapter

**Module docstring / summary:**

_No module docstring found._

### scripts.utils.cli

**File:** `scripts/utils/cli.py`

**Imports:** argparse

**Module docstring / summary:**

_No module docstring found._

**Functions:** base_parser

### src.resqme

**File:** `src/resqme/__init__.py`

**Imports:** –

**Module docstring / summary:**

_No module docstring found._

### src.resqme.config

**File:** `src/resqme/config.py`

**Imports:** dataclasses, dotenv, os

**Module docstring / summary:**

_No module docstring found._

**Classes:**

- `Paths` 

### src.resqme.pipelines.audio.audio_preprocess

**File:** `src/resqme/pipelines/audio/audio_preprocess.py`

**Imports:** os, pydub, typing

**Module docstring / summary:**

_No module docstring found._

**Functions:** to_wav

### src.resqme.pipelines.audio.audio_utils

**File:** `src/resqme/pipelines/audio/audio_utils.py`

**Imports:** numpy, soundfile

**Module docstring / summary:**

_No module docstring found._

**Functions:** add_white_noise

### src.resqme.pipelines.llm.data_adapter

**File:** `src/resqme/pipelines/llm/data_adapter.py`

**Imports:** types

**Module docstring / summary:**

Auto-generated adapter to run the user's original script inside a class without modifying its logic.
The original code is embedded as a raw string and executed in an isolated namespace.

**Classes:**

- `DataScript` 
  - Attributes: extra_globals
  - Methods: __init__, run

### src.resqme.pipelines.llm.generate_monologues

**File:** `src/resqme/pipelines/llm/generate_monologues.py`

**Imports:** argparse, csv, dataclasses, dotenv, openai, os, pandas, pathlib, random, time, typing

**Module docstring / summary:**

_No module docstring found._

**Classes:**

- `GenerationSpec` 
- `MonologueGenerator` 
  - Attributes: client, header, out_path, spec, symptom_df
  - Methods: __init__, _append_row_immediately, _build_prompt, _call_gpt, _present_symptoms_for, _sample_symptoms, diseases, from_csv, generate_for_disease, init_client, run_all

**Functions:** main, parse_args

### src.resqme.pipelines.llm.openai_adapter

**File:** `src/resqme/pipelines/llm/openai_adapter.py`

**Imports:** types

**Module docstring / summary:**

Auto-generated adapter to run the user's original script inside a class without modifying its logic.
The original code is embedded as a raw string and executed in an isolated namespace.

**Classes:**

- `OpenAIScript` 
  - Attributes: extra_globals
  - Methods: __init__, run

### src.resqme.pipelines.llm.tinyllama_adapter

**File:** `src/resqme/pipelines/llm/tinyllama_adapter.py`

**Imports:** types

**Module docstring / summary:**

Auto-generated adapter to run the user's original script inside a class without modifying its logic.
The original code is embedded as a raw string and executed in an isolated namespace.

**Classes:**

- `TinyLlamaScript` 
  - Attributes: extra_globals
  - Methods: __init__, run

### src.resqme.pipelines.tts.ElevenLabsTTS

**File:** `src/resqme/pipelines/tts/ElevenLabsTTS.py`

**Imports:** os, pandas, pathlib, pydub, random, requests, typing

**Module docstring / summary:**

ElevenLabsTTS wrapper class.
- Handles text-to-speech (TTS) generation.
- Supports batch synthesis from CSV with fixed or random voices.
- Supports adding new voices and uploading voice samples.
- Supports listing voices and saving them to CSV.

**Classes:**

- `ElevenLabsTTS` 
  - Attributes: api_key, base_url
  - Methods: __init__, _headers, add_samples, add_voice, list_voices, synthesize_from_csv, synthesize_text, synthesize_with_sfx

### src.resqme.pipelines.tts.tts_adapter

**File:** `src/resqme/pipelines/tts/tts_adapter.py`

**Imports:** types

**Module docstring / summary:**

Auto-generated adapter to run the user's original script inside a class without modifying its logic.
The original code is embedded as a raw string and executed in an isolated namespace.

**Classes:**

- `TTSScript` 
  - Attributes: extra_globals
  - Methods: __init__, run

### tests.test_monologue_gen

**File:** `tests/test_monologue_gen.py`

**Imports:** os, pandas, src.resqme.pipelines.llm.monologue_generator

**Module docstring / summary:**

_No module docstring found._

**Functions:** test_import_and_type

## Diagrams

### Classes (Mermaid)

```mermaid
classDiagram
class "src.resqme.config.Paths" {
}
class "src.resqme.pipelines.llm.tinyllama_adapter.TinyLlamaScript" {
  +extra_globals
  +__init__()
  +run()
}
class "src.resqme.pipelines.llm.generate_monologues.GenerationSpec" {
}
class "src.resqme.pipelines.llm.generate_monologues.MonologueGenerator" {
  +client
  +header
  +out_path
  +spec
  +symptom_df
  +__init__()
  +_append_row_immediately()
  +_build_prompt()
  +_call_gpt()
  +_present_symptoms_for()
  +_sample_symptoms()
  +diseases()
  +from_csv()
  +generate_for_disease()
  +init_client()
  +run_all()
}
class "src.resqme.pipelines.llm.data_adapter.DataScript" {
  +extra_globals
  +__init__()
  +run()
}
class "src.resqme.pipelines.llm.openai_adapter.OpenAIScript" {
  +extra_globals
  +__init__()
  +run()
}
class "src.resqme.pipelines.tts.tts_adapter.TTSScript" {
  +extra_globals
  +__init__()
  +run()
}
class "src.resqme.pipelines.tts.ElevenLabsTTS.ElevenLabsTTS" {
  +api_key
  +base_url
  +__init__()
  +_headers()
  +add_samples()
  +add_voice()
  +list_voices()
  +synthesize_from_csv()
  +synthesize_text()
  +synthesize_with_sfx()
}
```

### Imports (Mermaid)

```mermaid
flowchart LR
"tests.test_monologue_gen"
"scripts.llm.generate_with_openai"
"scripts.llm.generate_with_tinyllama"
"scripts.utils.cli"
"scripts.audio.preprocess_audio"
"scripts.audio.add_new_voice_ElevenLabs"
"scripts.audio.add_noise"
"scripts.tts.tts_elevenlabs"
"scripts.tts.tts_elevenlabs" --> "ResQme.src.resqme.pipelines.tts.ElevenLabsTTS"
"scripts.tts.tts_google"
"scripts.train.train_baseline"
"scripts.eval.evaluate_baseline"
"src.resqme.config"
"src.resqme"
"src.resqme.pipelines.llm.tinyllama_adapter"
"src.resqme.pipelines.llm.generate_monologues"
"src.resqme.pipelines.llm.data_adapter"
"src.resqme.pipelines.llm.openai_adapter"
"src.resqme.pipelines.audio.audio_utils"
"src.resqme.pipelines.audio.audio_preprocess"
"src.resqme.pipelines.tts.tts_adapter"
"src.resqme.pipelines.tts.ElevenLabsTTS"
```
