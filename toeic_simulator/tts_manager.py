"""TTS Manager — pyttsx3 in a background thread with interrupt support."""
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class TTSManager(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._thread: threading.Thread | None = None
        self._interrupted: bool = False
        self._current_engine = None          # pyttsx3 engine currently running
        self._engine_lock = threading.Lock() # protects _current_engine

    def speak(self, text: str) -> None:
        """Speak text asynchronously; emits finished when done (unless interrupted)."""
        if not text or not text.strip():
            self.finished.emit()
            return

        self._interrupted = False            # reset before new utterance

        def _run(t: str) -> None:
            _engine = None
            try:
                import pyttsx3
                _engine = pyttsx3.init()
                with self._engine_lock:
                    self._current_engine = _engine

                _engine.setProperty("rate", 145)
                try:
                    voices = _engine.getProperty("voices") or []
                    for v in voices:
                        vid   = (v.id   or "").lower()
                        vname = (v.name or "").lower()
                        if any(k in vid or k in vname
                               for k in ("en_us", "english", "zira", "david", "hazel")):
                            _engine.setProperty("voice", v.id)
                            break
                except Exception:
                    pass

                _engine.say(t)
                _engine.runAndWait()

            except Exception as exc:
                print(f"[TTS] Error: {exc}")
            finally:
                with self._engine_lock:
                    self._current_engine = None
                try:
                    if _engine is not None:
                        _engine.stop()
                except Exception:
                    pass
                if not self._interrupted:
                    self.finished.emit()

        self._thread = threading.Thread(target=_run, args=(text,), daemon=True)
        self._thread.start()

    def interrupt(self) -> None:
        """
        Signal the TTS thread to abort.  Sets the interrupted flag so finished
        is NOT emitted.  Also tries to stop the pyttsx3 engine immediately.
        """
        self._interrupted = True
        with self._engine_lock:
            engine = self._current_engine
        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass
