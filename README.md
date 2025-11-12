# 1112 Most Common Italian Words — Anki Deck (with audio & examples)

This repository contains a curated list of common Italian words, 5 example sentences per word, generated audio files, and an Anki deck for study. The project pipeline is split into three main steps: extract words, generate example sentences (AI), and produce audio + Anki deck.

## About
- Target level: A2 / beginner vocabulary and examples.
- Example sentences were generated using the free tier of OpenRouter.
- Visuals: adding an image per vocab card is recommended — visual memory helps retention.

## Quick summary
- Word source: data/italian_1112_words.txt
- Sentence generation (AI batching): italian_sentences_generator.py
- Audio generation: audio_generator.py
- Anki deck (notebook): Italian_Anki_Deck_Generation.ipynb
- Final Anki package: Anki/1112_most_common_italian_vocabs.apkg

## Features
- Extract raw words from the web and save CSV/JSON/TXT.
- Batch AI generation of multiple example sentences (handles verbs specially).
- gTTS + pydub audio generation for word + examples with pauses.
- Genanki notebook to assemble deck with media.
- Optional: add AI-generated images to cards for better visual learning.

## Prerequisites
- Python 3.8+
- pip packages: requests, beautifulsoup4, gTTS, pydub, genanki, langdetect
  Example:
  ```sh
  pip install requests beautifulsoup4 gTTS pydub genanki langdetect
  ```

## Important notes about recent changes
- Sentence generation now uses batch AI via OpenRouter and may require updating API keys and model settings. See configuration in [`italian_sentences_generator.py`](italian_sentences_generator.py).
- Batch sizes and token accounting are conservative; adjust `calculate_optimal_batch_size` if you need different behavior.
- If your pipeline previously handled 200 words per run but now fails, check rate-limits, the OpenRouter credits, and the `max_tokens` / `temperature` params in the AI call.

## Usage (recommended order)

1) Extract words (if you need to re-scrape)
```sh
python italian_words_extractor.py
```
- Produces: `data/italian_1112_words.csv`, `data/italian_1112_words.json`, `data/italian_1112_words.txt`, `data/italian_words_only.txt`

2) Generate example sentences (AI batching)
```sh
python italian_sentences_generator.py
```
- Input: `./data/italian_1112_words.txt`
- Output: `data/italian_vocabulary_with_examples.txt`
- Configure your OpenRouter key at the top of [`italian_sentences_generator.py`](italian_sentences_generator.py) as `OPENROUTER_API_KEY`.

3) Create audio for each word + examples
```sh
python audio_generator.py
```
- Uses gTTS + pydub; audio files are written to `audio_files/` as `{word}.mp3`.
- Ensure `ffmpeg` is installed and on PATH for pydub.

4) Build the Anki deck
- Run `Italian_Anki_Deck_Generation.ipynb` in Jupyter/Colab.
- The notebook uses `genanki` to create the deck and collects media from `audio_files/` (and optionally `images/`).
- Final deck written to: `Anki/1112_most_common_italian_vocabs.apkg`.

Contributing
- Questions are welcome: open an Issue for bugs, questions, or requests.
- Pull requests are welcome for improvements, fixes, or added assets.
- Add images for visual learning: place image files in the images/ folder and name each file exactly as the vocab token (e.g., images/cane.jpg for the word "cane"). If you add images, update the notebook or script that builds the deck to include images as media (the notebook reads media lists — search for `media_files` in the notebook).
- If you generate images with AI, include a short README in images/ describing the generator and license for those images.
- Keep changes small and focused; include tests or a brief usage note when changing scripts.

Notes & Tips
- This collection is aimed at A2 / beginner learners — examples use straightforward language.
- Example sentences were generated with the free OpenRouter plan; quality is good for study-level examples but please review and correct any errors before wide distribution.
- Adding one clear, simple image per word improves recall — try 1:1 pictorial representation, avoid complex scenes.
- If you need help wiring images into the final Anki deck, open an Issue and include the file naming convention you used; guidance will be provided.

Troubleshooting
- AI Authorization / Limits: check `OPENROUTER_API_KEY` and OpenRouter credits; `test_api_connection()` in `italian_sentences_generator.py` will help diagnose.
- Rate limits: reduce batch size, add delays between requests.
- Parsing issues: review the printed `Response preview:` when `parse_batch_response` fails.
- Audio issues: pydub requires ffmpeg; install ffmpeg and ensure it is on PATH.
- File encodings: all scripts use UTF-8; ensure your environment supports it.

Files in this repository
- [audio_generator.py](audio_generator.py)
- [Italian_Anki_Deck_Generation.ipynb](Italian_Anki_Deck_Generation.ipynb)
- [italian_sentences_generator.py](italian_sentences_generator.py)
- [italian_words_extractor.py](italian_words_extractor.py)
- [README.md](README.md)
- [Anki/1112_most_common_italian_vocabs.apkg](Anki/1112_most_common_italian_vocabs.apkg)
- [audio_files/](audio_files/)
- [images/](images/) — optional images for cards
- [data/italian_1112_words.csv](data/italian_1112_words.csv)
- [data/italian_1112_words.json](data/italian_1112_words.json)
- [data/italian_1112_words.txt](data/italian_1112_words.txt)
- [data/italian_vocabulary_with_examples.txt](data/italian_vocabulary_with_examples.txt)
- [data/italian_words_only.txt](data/italian_words_only.txt)

License
- MIT