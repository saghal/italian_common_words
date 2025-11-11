from gtts import gTTS
from pydub import AudioSegment
import os
import time

# Create a folder for audio files
audio_folder = 'audio_files'
os.makedirs(audio_folder, exist_ok=True)

def create_speech_file(word, examples):
    """
    Generate audio for Italian word and sentences only (no English)
    Add 1.5 second pause between sentences
    """
    try:
        audio_segments = []

        # Generate audio for the word first
        word_audio_path = f"temp_word_{word}.mp3"
        tts_word = gTTS(text=word, lang='it', slow=False)
        tts_word.save(word_audio_path)
        audio_segments.append(AudioSegment.from_file(word_audio_path))

        # Add 1.5 second pause after the word
        silence = AudioSegment.silent(duration=1500)
        audio_segments.append(silence)

        # Generate audio for each Italian sentence with pauses
        for idx, sentence in enumerate(examples):
            temp_path = f"temp_sentence_{word}_{idx}.mp3"
            tts_sentence = gTTS(text=sentence, lang='it', slow=False)
            tts_sentence.save(temp_path)

            # Add the sentence audio
            audio_segments.append(AudioSegment.from_file(temp_path))

            # Add 1.5 second pause between sentences (but not after the last one)
            if idx < len(examples) - 1:
                audio_segments.append(silence)

            # Clean up temp file
            os.remove(temp_path)

        # Combine all audio segments
        combined_audio = sum(audio_segments)

        # Save with JUST the word name - no prefix!
        filename = os.path.join(audio_folder, f"{word}.mp3")
        combined_audio.export(filename, format="mp3")

        # Clean up word temp file
        os.remove(word_audio_path)

        duration = len(combined_audio) / 1000
        print(f"✓ Created {word}.mp3 ({duration:.1f}s)")
        return filename

    except Exception as e:
        print(f"✗ Error creating audio for '{word}': {e}")
        return None

# Read the Italian words and examples from the file
input_file = './data/italian_vocabulary_with_examples.txt'

print(f"Reading from: {input_file}")
with open(input_file, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Variables to store current word and Italian examples
current_word = ""
current_italian_examples = []
files_created = 0
files_failed = 0

# Process the lines
i = 0
while i < len(lines):
    line = lines[i].strip()

    if not line:
        i += 1
        continue

    # Check if line contains word definition
    if '[' in line and ']' in line and '-' in line:
        # If we have a previous word, create audio for it
        if current_word and current_italian_examples:
            result = create_speech_file(current_word, current_italian_examples)
            if result:
                files_created += 1
            else:
                files_failed += 1

            # Wait to avoid rate limiting (3 seconds is safer)
            time.sleep(3)

            # Progress update every 50 words
            if files_created % 50 == 0:
                print(f"\n--- Progress: {files_created} files created ---\n")

        # Extract the word (before the bracket)
        current_word = line.split('[')[0].strip()
        current_italian_examples = []
        i += 1
    else:
        # This is an Italian sentence (English translation is on next line)
        if i + 1 < len(lines):
            italian_sentence = line
            current_italian_examples.append(italian_sentence)
            i += 2  # Skip both Italian and English lines
        else:
            i += 1

# Create audio for the last word
if current_word and current_italian_examples:
    result = create_speech_file(current_word, current_italian_examples)
    if result:
        files_created += 1
    else:
        files_failed += 1

print(f"\n{'='*50}")
print(f"Audio generation complete!")
print(f"✓ Files created: {files_created}")
print(f"✗ Files failed: {files_failed}")
print(f"Total: {files_created + files_failed}")
print(f"{'='*50}")

# List some examples
audio_files = os.listdir(audio_folder)
print(f"\nFirst 10 audio files created:")
for filename in sorted(audio_files)[:10]:
    print(f"  - {filename}")