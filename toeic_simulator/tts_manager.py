"""TTS Manager - runs pyttsx3 in a background thread, emits finished signal."""
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class TTSManager(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._thread: threading.Thread | None = None

    def speak(self, text: str) -> None:
        """Speak text asynchronously; emits finished when done."""
        if not text or not text.strip():
            self.finished.emit()
            return

        def _run(t: str) -> None:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", 145)
                # Prefer an English voice if available
                try:
                    voices = engine.getProperty("voices") or []
                    for v in voices:
                        vid = (v.id or "").lower()
                        vname = (v.name or "").lower()
                        if any(k in vid or k in vname
                               for k in ("en_us", "english", "zira", "david", "hazel")):
                            engine.setProperty("voice", v.id)
                            break
                except Exception:
                    pass
                engine.say(t)
                engine.runAndWait()
                try:
                    engine.stop()
                except Exception:
                    pass
            except Exception as exc:
                print(f"[TTS] Error: {exc}")
            finally:
                self.finished.emit()

        self._thread = threading.Thread(target=_run, args=(text,), daemon=True)
        self._thread.start()
