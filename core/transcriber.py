import os
import requests
from faster_whisper import WhisperModel
from pydub import AudioSegment

SARVAM_PIECE_SECONDS = 25
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


# Function to load the faster Whisper model
def load_model():
    global _model

    if _model is None:
        print(
            f"Loading Whisper model: {WHISPER_MODEL} "
            f"on {WHISPER_DEVICE}..."
        )

        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE
        )

        print("Whisper model loaded.")

    return _model


# Function to transcribe one audio chunk using faster-whisper
def transcribe_chunk_whisper(chunk_path: str) -> str:
    model = load_model()

    segments, info = model.transcribe(
        chunk_path,
        task="transcribe",
        beam_size=1,
        vad_filter=True
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )

    return text.strip()


# Function to send one audio piece to Sarvam
def _send_to_sarvam(piece_path: str) -> str:
    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    with open(piece_path, "rb") as f:
        files = {
            "file": (
                os.path.basename(piece_path),
                f,
                "audio/wav"
            )
        }

        data = {
            "model": SARVAM_MODEL,
            "with_diarization": "false"
        }

        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

    if not response.ok:
        print(f"\n❌ Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "").strip()


# Function to transcribe one chunk using Sarvam
def transcribe_chunk_sarvam(chunk_path: str) -> str:
    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    transcripts = []

    for i, start in enumerate(
        range(0, len(audio), piece_ms)
    ):
        piece = audio[start:start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"

        piece.export(
            piece_path,
            format="wav"
        )

        try:
            print(
                f"  → Sarvam piece "
                f"{i + 1}/{total_pieces} ..."
            )

            text = _send_to_sarvam(piece_path)

            if text:
                transcripts.append(text)

        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return " ".join(transcripts).strip()


# Function to select the transcription engine
def transcribe_chunk(
    chunk_path: str,
    language: str = "english"
) -> str:
    language = language.lower()

    if language == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)

    if language == "english":
        return transcribe_chunk_whisper(chunk_path)

    raise ValueError(
        f"Unsupported language: {language}. "
        "Use 'english' or 'hinglish'."
    )


# Function to transcribe all audio chunks
def transcribe_all(
    chunks: list,
    language: str = "english"
) -> str:
    engine = (
        "Sarvam AI"
        if language.lower() == "hinglish"
        else "Faster-Whisper"
    )

    print(f"Using {engine} for transcription.")

    transcripts = []

    for i, chunk in enumerate(chunks, start=1):
        print(
            f"Transcribing chunk "
            f"{i}/{len(chunks)}..."
        )

        text = transcribe_chunk(
            chunk,
            language=language
        )

        if text:
            transcripts.append(text)

    print("Transcription complete.")

    return " ".join(transcripts).strip()