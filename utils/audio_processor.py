import os
import re
import yt_dlp
from pydub import AudioSegment

# Configuration
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Sanitize filename
def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = filename.strip().rstrip(". ")
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4",
        "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    if filename.upper() in reserved_names:
        filename = f"_{filename}"
    return filename or "audio"

# Download YouTube audio
def download_youtube_audio(url: str) -> str:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        title = info_dict.get("title", "audio")
        safe_title = sanitize_filename(title)
        mp3_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}.mp3")
        original_path = ydl.prepare_filename(info_dict)
        original_mp3 = os.path.splitext(original_path)[0] + ".mp3"

        if os.path.exists(original_mp3):
            if original_mp3 != mp3_path:
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                os.rename(original_mp3, mp3_path)

        if not os.path.exists(mp3_path):
            raise FileNotFoundError(f"Downloaded audio not found: {mp3_path}")

        return mp3_path

# Convert audio to WAV
def convert_audio_to_wav(input_file: str) -> str:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Audio file not found: {input_file}")

    output_file = os.path.splitext(input_file)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_file, format="wav")
    print(f"WAV file created: {output_file}")
    return output_file

# Split audio into chunks
def chunk_audio_file(input_file: str, chunk_length_minute: int = 10) -> list:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Audio file not found: {input_file}")

    if chunk_length_minute <= 0:
        raise ValueError("chunk_length_minute must be greater than 0")

    audio = AudioSegment.from_file(input_file)
    chunk_length_ms = chunk_length_minute * 60 * 1000
    chunks = []

    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_file = os.path.splitext(input_file)[0] + f"_chunk_{i // chunk_length_ms}.wav"
        chunk.export(chunk_file, format="wav")
        chunks.append(chunk_file)

    return chunks

# Process input
def process_input(source: str) -> list:
    source = source.strip()

    if not source:
        raise ValueError("Audio source cannot be empty")

    if source.startswith(("http://", "https://")):
        print("Detected YouTube URL. Downloading audio...")
        mp3_path = download_youtube_audio(source)
        print("Converting audio to WAV...")
        wav_path = convert_audio_to_wav(mp3_path)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_audio_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio_file(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
