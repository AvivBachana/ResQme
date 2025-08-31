.PHONY: gen-openai gen-tiny tts noise preprocess train eval all

gen-openai:
	python scripts/llm/generate_with_openai.py

gen-tiny:
	python scripts/llm/generate_with_tinyllama.py

tts:
	python scripts/tts/tts_google.py

noise:
	python scripts/audio/add_noise.py

preprocess:
	python scripts/audio/preprocess_audio.py

train:
	python scripts/train/train_baseline.py

eval:
	python scripts/eval/evaluate_baseline.py

all: gen-openai tts noise preprocess train eval
