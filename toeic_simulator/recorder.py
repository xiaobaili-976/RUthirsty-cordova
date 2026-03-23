"""
RecorderManager — microphone recording + offline speech-to-text (vosk).

Behaviour:
  • If pyaudio is not installed / no mic found → available=False, all calls are no-ops.
  • If vosk model not found in <base_dir>/model/ → audio saved, STT skipped.
  • Recording is written to <base_dir>/records/<subdir>/<hint>_<timestamp>.wav
  • Transcript (if STT available) written alongside as .txt

This module imports pyaudio and vosk lazily so missing packages never
crash the main process.
"""
import json
import os
import threading
import wave
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal


class RecorderManager(QObject):
    # Emitted when transcription finishes (wav_path, text)
    transcription_ready = pyqtSignal(str, str)
    # Emitted once during init to report mic availability
    mic_available = pyqtSignal(bool)

    RATE     = 16_000
    CHANNELS = 1
    CHUNK    = 1024

    def __init__(self, base_dir: str):
        super().__init__()
        self._base_dir   = base_dir
        self._recording  = False
        self._frames: list[bytes] = []
        self._current_wav = ""
        self.available    = False   # True if pyaudio + mic ready
        self._model       = None    # vosk.Model or None

        self._detect_mic()
        self._load_model()

    # ── public API ────────────────────────────────────────────────────────────
    def start_recording(self, subdir: str, hint: str) -> None:
        """Start mic recording.  Files saved to <base_dir>/<subdir>/."""
        if not self.available or self._recording:
            return
        rec_dir = os.path.join(self._base_dir, subdir)
        os.makedirs(rec_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_wav = os.path.join(rec_dir, f"{hint}_{ts}.wav")
        self._recording   = True
        self._frames      = []
        threading.Thread(target=self._record_loop, daemon=True).start()

    def stop_recording(self) -> None:
        """Signal the recording thread to stop; saving + STT happen in background."""
        self._recording = False

    # ── private ───────────────────────────────────────────────────────────────
    def _detect_mic(self) -> None:
        try:
            import pyaudio  # noqa: F401  (lazy import test)
            pa = __import__("pyaudio").PyAudio()
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    self.available = True
                    break
            pa.terminate()
        except Exception as exc:
            print(f"[Recorder] pyaudio unavailable: {exc}")

    def _load_model(self) -> None:
        model_dir = os.path.join(self._base_dir, "model")
        if not os.path.isdir(model_dir):
            print("[Recorder] No vosk model found — STT disabled.")
            return
        try:
            from vosk import Model  # type: ignore
            self._model = Model(model_dir)
            print("[Recorder] vosk model loaded.")
        except Exception as exc:
            print(f"[Recorder] vosk unavailable: {exc}")

    def _record_loop(self) -> None:
        import pyaudio
        pa     = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )
        while self._recording:
            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                self._frames.append(data)
            except Exception:
                break
        stream.stop_stream()
        stream.close()
        pa.terminate()

        if not self._frames:
            return

        # ── Save WAV ──────────────────────────────────────────────────────────
        wav_path = self._current_wav
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)   # 16-bit PCM
            wf.setframerate(self.RATE)
            wf.writeframes(b"".join(self._frames))
        print(f"[Recorder] Saved {wav_path}")

        # ── Transcribe in background ──────────────────────────────────────────
        if self._model is not None:
            threading.Thread(
                target=self._transcribe, args=(wav_path,), daemon=True
            ).start()

    def _transcribe(self, wav_path: str) -> None:
        try:
            from vosk import KaldiRecognizer  # type: ignore
            rec = KaldiRecognizer(self._model, self.RATE)
            with wave.open(wav_path, "rb") as wf:
                while True:
                    data = wf.readframes(4_000)
                    if not data:
                        break
                    rec.AcceptWaveform(data)
            result = json.loads(rec.FinalResult())
            text   = result.get("text", "").strip()
            if text:
                txt_path = wav_path.replace(".wav", ".txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.transcription_ready.emit(wav_path, text)
                print(f"[Recorder] Transcript saved: {text[:60]}")
        except Exception as exc:
            print(f"[Recorder] STT error: {exc}")
